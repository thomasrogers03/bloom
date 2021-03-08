# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import traceback

if __name__ == "__main__":
    try:
        from bloom.main import main

        main()
    except Exception as error:
        print(
            f"Unable to run Bloom due to {error}, saving crash information to crash.log"
        )
        with open("crash.log", "w+") as file:
            file.write(str(error))
            file.write(traceback.format_exc())
