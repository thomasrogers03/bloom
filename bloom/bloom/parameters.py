import argparse

def get_parameters():
    parser = argparse.ArgumentParser(description='Blood modding suite')
    parser.add_argument(
        '--direct-tools', 
        action='store_true',
        help='Turn on Panda3d direct tools'
    )
    parser.add_argument(
        'map_path',
        nargs='?',
        help='Map to load'
    )

    return parser.parse_args()
