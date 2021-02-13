# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0


class EditMode:
    def set_editor(self, editor):
        raise NotImplementedError

    def enter_mode(self, state: dict):
        raise NotImplementedError

    def tick(self):
        raise NotImplementedError

    def exit_mode(self):
        raise NotImplementedError
