import glob
import logging
import os
import re
import tempfile
import typing

from antlr4 import *

from bloom.parsers.ActorLexer import ActorLexer
from bloom.parsers.ActorListener import ActorListener
from bloom.parsers.ActorParser import ActorParser

logging.basicConfig(
    level='INFO',
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Actor:

    def __init__(self):
        self.properties = []
        self.type = None


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
        property_definition = {
            'name': ctx.property_name().getText(),
            'value': ctx.property_value().getText(),
        }
        self._current_actor.properties.append(property_definition)

    def exitActor(self, ctx: ActorParser.ActorContext):
        self._current_actor.type = ctx.INT().getText()

        self._actors.append(self._current_actor)
        self._current_actor = None


class Loader:

    def __init__(self, paths: typing.List[str]):
        self._paths = paths

    def load_actors(self):
        all_actors = []
        for actor_path in self._paths:
            actors = self._process_file(actor_path)
            all_actors += actors

        return all_actors

    @staticmethod
    def _extend_lines(lines: typing.List[str]):
        result = []
        updated_line = ''

        for line in lines:
            updated_line += line
            if line[-2:-1] == '\\':
                updated_line = updated_line[:-2]
            else:
                result.append(updated_line)
                updated_line = ''
        result.append(updated_line)

        return result

    def _pre_process_file(self, path: str, defines):
        logger.info(f'Preprocessing {path}')

        with open(path, 'r') as file:
            lines = file.readlines()

        lines = self._extend_lines(lines)

        result = ''
        for line in lines:
            match = re.match('^\s*#(.*)$', line)
            if match:
                preprocessor = match[1]
                include = re.match('^include "([^"]+)"$', preprocessor)
                if include:
                    result += self._pre_process_file(include[1], defines)
                    continue

                define = re.match('^define\s+([^\s]+)\s+(.*)?$', preprocessor)
                if define:
                    definer = re.escape(define[1])
                    definer = re.compile(f'\s+{definer}\s+')
                    value = f' {define[2].strip()} '
                    defines.append((definer, value))
                    continue

                raise ValueError(f'Unexpected preprocessor {preprocessor}')
            else:
                line = re.sub('//.*$', '', line)
                for definer, value in defines:
                    line = re.sub(definer, value, line)

                line = line.strip()
                if line:
                    result += line + '\n'

        return result

    def _process_file(self, path: str):
        defines = []
        pre_processed = self._pre_process_file(path, defines)

        logger.info(f'Loading actors from {path}')
        with tempfile.NamedTemporaryFile() as file:
            file.write(pre_processed.encode())
            file.flush()

            logger.info(f'Parsing {path}')
            input_stream = FileStream(file.name)
            lexer = ActorLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = ActorParser(stream)
            tree = parser.program()

            listener = Listener()
            walker = ParseTreeWalker()
            walker.walk(listener, tree)

        return listener.actors


def main():
    os.chdir('kpx')
    paths = [
        actor_path
        for actor_path in glob.glob('defs/actors/*.txt')
    ]

    logger.info('Loading actors')
    all_actors = Loader(paths).load_actors()
    logger.info(f'{len(all_actors)} actors found')


if __name__ == '__main__':
    main()
