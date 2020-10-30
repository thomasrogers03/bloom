# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0


if __name__ == '__main__':
    try:
        from bloom.main import main

        main()
    except Exception as error:
        print(f'Unable to run Bloom due to {error}')