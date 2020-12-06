# BlooM - Blood Modding Suite

BlooM is a project aimed toward bringing modern modding tools into Blood, while supporting the original game limitations as much as possible. 

If you've not worked with any Blood modding tools (such as mapedit) before, I highly recommend looking into some documentation for those tools, as the BlooM documentation will focus on the specifics of this tool itself, rather than Blood modding as a whole. I personally recommend [RTCM](http://www.r-t-c-m.com/), particularly [here](http://www.r-t-c-m.com/knowledge-base/downloads-rtcm/blood-faqs-mapedit/). I've personally found a lot of help from these resources over the years in learning more about Blood.

## [Latest Releases](https://github.com/thomasrogers03/bloom/releases)

### Requirements

- Blood - can be purchased [here](https://store.steampowered.com/app/1010750/Blood_Fresh_Supply/) and [here](https://www.gog.com/game/blood_fresh_supply)
- [fluidsynth](http://www.fluidsynth.org/) and a sound font

### Installing

If you're on Windows, you can just download `bloom-V.V.V_win_amd64.zip` (where `V.V.V` is ther version) and it should work out of the box.

Otherwise you'll have to download the `bloom-V.V.V-py3-none-any.whl` file, install and run it as a Python module under your platform. See the [pip](https://pip.pypa.io/en/stable/quickstart/) documentation for how to install. After that you can run it from a terminal by doing `python -m bloom`.

**note that BlooM requires python>=3.6 to run**

## First Run

Upon running BlooM for the first time, you'll be prompted with a few dialogs, asking you for the following paths:

- Blood game path
- Fluidsynth path (usually something like C:\fluidsynth-x64\bin if on Windows) if it cannot be automatically detected
- Soundfont path (usually something like C:\soundfonts\default.sf2 on Windows)

## Features

![Demo Map](docs/BMDEMO.PNG)

Currently it supports:
- mouse based navigation
- basic map layout editing
    - editing in 2d and 3d
    - adding and modifying sector shapes
    - changing textures
    - joining sectors
    - and more...
- sprite editing
    - moving in 2d and 3d
    - categorized sprite types
    - property editing with friendly names
    - categorized sounds
    - and more...
- sector special editing
    - indicators for motion
    - property editing
- easy to build room over room
- triggers
    - remove the need for manually specifying tx/rx ids
    - just link triggered objects to the objects that trigger them
- sound previews using openal and [fluidsynth](https://github.com/FluidSynth/fluidsynth)

Planned Features:
- undo
- categorized textures
- special wall types
- explosion sequence builder
- easy environmental effects (rain, snow, etc.)
- scripted sequence tools (for things like puzzles)
- easy mod ini building
- support for quickly running maps/mods in ports
- SEQ editting support
- QAV editting support

## Documentation For Specific Features

### [Navigation](docs/NAVIGATION.md)
### [Editing Geometry](docs/MAP_GEOMETRY.md)
### [Editing Sprites](docs/SPECIAL_SPRITES.md)
### [Editing Sectors](docs/SPECIAL_SECTORS.md)
### [Changing Textures](docs/TEXTURES.md)
### [Room Over Room](docs/ROR.md)
### [Triggering Effects](docs/TRIGGERS.md)

## Building

Building BlooM is pretty easy, all you have to do is run the included `build.sh` script.

**note: if on Windows, you may need something like [git-bash](https://gitforwindows.org/) or [wsl](https://docs.microsoft.com/en-us/windows/wsl/about) to run it**

**note 2: you can only generate the Windows binaries from Windows, any builds created by other platforms will not work correctly**

## Running Tests

BlooM has some basic tests that can be run by executing `run_tests.sh bloom.tests`. See [above](##building) for notes on running shell scripts on Windows.

## Known Issues:

BlooM is not without it's problems, so I'll list the ones I know about below:

- Sometimes joining 2 walls together doesn't work correctly, causing the sectors to have the incorrect shape after the join
- Sometimes splitting sectors does not result in the correct sector shapes
- Art from Cryptic Passage isn't loaded correctly
- Audio doesn't stop playing when BlooM is not the active window
- Visibility clipping doesn't always work as expected, leading to visual artifacts