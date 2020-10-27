import argparse

def get_parameters():
    parser = argparse.ArgumentParser(description='Blood modding suite')
    parser.add_argument(
        'map_path',
        nargs='?',
        help='Map to load'
    )

    return parser.parse_args()
