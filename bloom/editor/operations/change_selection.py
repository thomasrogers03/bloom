# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from ..highlighting import highlight_details
from .undo_stack import UndoableOperation

class Selector:
    
    def set_selected(self, selection: typing.List[highlight_details.HighlightDetails]):
        raise NotImplementedError()

class ChangeSelection(UndoableOperation):

    def __init__(
        self, 
        selector: Selector,
        previous_selection: typing.List[highlight_details.HighlightDetails], 
        new_selection: typing.List[highlight_details.HighlightDetails]
    ):
        self._selector = selector
        self._previous_selection = previous_selection
        self._new_selection = new_selection
        self.apply = self.redo

    def get_name(self):
        return 'Select'

    def undo(self):
        self._selector.set_selected(self._previous_selection)

    def redo(self):
        self._selector.set_selected(self._new_selection)


