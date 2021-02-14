import glob
import logging
import os
import re
import tempfile
import typing

import yaml
from antlr4 import *

from bloom.parsers.ActorLexer import ActorLexer
from bloom.parsers.ActorListener import ActorListener
from bloom.parsers.ActorParser import ActorParser

logging.basicConfig(
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Actor:
    def __init__(self):
        self.properties = {}
        self.type = -1


class Listener(ActorListener):
    def __init__(self):
        super().__init__()
        self._actors = []
        self._current_actor = None

    @property
    def actors(self):
        return self._actors

    def enterActor(self, ctx: ActorParser.ActorContext):
        self._current_actor = Actor()

    def exitProperty_definition(self, ctx: ActorParser.Property_definitionContext):
        name = ctx.property_name().getText()
        value = ctx.property_value().getText()
        self._current_actor.properties[name] = value

    def exitActor(self, ctx: ActorParser.ActorContext):
        self._current_actor.type = int(ctx.INT().getText())

        self._actors.append(self._current_actor)
        self._current_actor = None


class Loader:
    class PreprocessedFile(typing.NamedTuple):
        code: str
        defines: dict

    def __init__(self, paths: typing.List[str]):
        self._paths = paths
        self._preprocessed_cache: typing.Dict[str, self.PreprocessedFile] = {}

    def load_actors(self):
        all_actors: typing.List[Actor] = []
        for actor_path in self._paths:
            actors = self._process_file(actor_path)
            all_actors += actors

        return all_actors

    def get_sfx_defines(self):
        return {
            key: int(value)
            for preprocessed in self._preprocessed_cache.values()
            for key, value in preprocessed.defines.items()
            if key.startswith("SFX_")
        }

    @staticmethod
    def _extend_lines(lines: typing.List[str]):
        result = []
        updated_line = ""

        for line in lines:
            updated_line += line
            if line[-2:-1] == "\\":
                updated_line = updated_line[:-2]
            else:
                result.append(updated_line)
                updated_line = ""
        result.append(updated_line)

        return result

    def _pre_process_file(self, path: str, defines: dict):
        if path in self._preprocessed_cache:
            logger.info(f"{path} found in preprocessed cache")
            cached = self._preprocessed_cache[path]
            defines.update(cached.defines)
            return cached.code

        logger.info(f"Preprocessing {path}")

        with open(path, "r") as file:
            lines = file.readlines()

        lines = self._extend_lines(lines)

        result = ""
        current_defines = dict(defines)
        for line in lines:
            match = re.match("^\s*#(.*)$", line)
            if match:
                preprocessor = match[1]
                include = re.match('^include "([^"]+)"$', preprocessor)
                if include:
                    result += self._pre_process_file(include[1], defines)
                    continue

                define = re.match("^define\s+([^\s]+)\s+(.*)?$", preprocessor)
                if define:
                    defines[define[1]] = self._macro_fill(define[2].strip(), defines)
                    continue

                raise ValueError(f"Unexpected preprocessor {preprocessor}")
            else:
                line = re.sub("//.*$", "", line)
                line = self._macro_fill(line, defines)
                if line:
                    result += line + "\n"

        new_defines = {key: defines[key] for key in set(defines) - set(current_defines)}
        self._preprocessed_cache[path] = self.PreprocessedFile(result, new_defines)
        return result

    @staticmethod
    def _macro_fill(line: str, defines: typing.Dict[str, str]):
        words = [word.strip() for word in line.split()]
        words = [defines.get(word, word) for word in words]
        return " ".join(words)

    def _process_file(self, path: str):
        pre_processed = self._pre_process_file(path, {})

        logger.info(f"Loading actors from {path}")
        with tempfile.NamedTemporaryFile() as file:
            file.write(pre_processed.encode())
            file.flush()

            logger.info(f"Parsing {path}")
            input_stream = FileStream(file.name)
            lexer = ActorLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = ActorParser(stream)
            tree = parser.program()

            listener = Listener()
            walker = ParseTreeWalker()
            walker.walk(listener, tree)

        return listener.actors


def _load_sprite_type(actor: Actor, sprite: dict):
    logger.info(f"Getting sprite {actor.type} info")

    if "sprite.clipdist" in actor.properties:
        sprite["clipdist"] = float(actor.properties["sprite.clipdist"])

    if "sprite.pal" in actor.properties:
        sprite["palette"] = int(actor.properties["sprite.pal"])

    if "repeats" not in sprite:
        sprite["repeats"] = {}

    if "sprite.xrepeat" in actor.properties:
        sprite["repeats"]["x"] = round(int(actor.properties["sprite.xrepeat"]) / 4)

    if "sprite.yrepeat" in actor.properties:
        sprite["repeats"]["y"] = round(int(actor.properties["sprite.yrepeat"]) / 4)

    if "sprite.blocking" in actor.properties:
        sprite["blocking"] = int(actor.properties["sprite.blocking"])

    if "actor.spawnSeq" in actor.properties:
        sprite["seq"] = int(actor.properties["actor.spawnSeq"])


def _process_actors(all_actors: typing.List[Actor]):
    with open("bloom/resources/sprite_types.yaml", "r") as file:
        sprite_types = yaml.safe_load(file.read())

    for actor in all_actors:
        if actor.type not in sprite_types:
            sprite_types[actor.type] = {
                "category": "decoration",
                "name": "Unknown",
                "tile_config": {"tile": 0},
            }
        _load_sprite_type(actor, sprite_types[actor.type])

    with open("bloom/resources/sprite_types.yaml", "w+") as file:
        file.write(yaml.safe_dump(sprite_types))


def _process_sounds(sfx_definitions: typing.Dict[str, int]):
    with open("bloom/resources/sound_names.yaml", "r") as file:
        sounds = yaml.safe_load(file.read())

    for name, sfx in sfx_definitions.items():
        if sfx not in sounds:
            logger.info(f"Adding sound {sfx}: {name}")
            sounds[sfx] = {
                "name": name,
                "category": "unknown",
            }

    with open("bloom/resources/sound_names.yaml", "w+") as file:
        file.write(yaml.safe_dump(sounds))


def main():
    previous_directory = os.getcwd()
    os.chdir("kpf")

    paths = [actor_path for actor_path in glob.glob("defs/actors/*.txt")]

    loader = Loader(paths)
    logger.info("Loading actors")
    all_actors = loader.load_actors()
    logger.info(f"{len(all_actors)} actors found")

    os.chdir(previous_directory)

    _process_actors(all_actors)
    _process_sounds(loader.get_sfx_defines())


if __name__ == "__main__":
    main()
