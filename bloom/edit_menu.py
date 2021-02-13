import tkinter


class EditMenu:
    _MENU_NAME = "Edit"

    def __init__(self, menu_bar: tkinter.Menu):
        self._menu_bar = menu_bar
        self._edit_menu = self._make_menu()
        self._menu_bar.add_cascade(label=self._MENU_NAME, menu=self._edit_menu)
        self._index = self._menu_bar.index(self._MENU_NAME)

    def clear(self):
        self._edit_menu.destroy()
        self._edit_menu = None
        self._menu_bar.delete(self._MENU_NAME)

        self._edit_menu = self._make_menu()
        self._menu_bar.insert_cascade(
            self._index, label=self._MENU_NAME, menu=self._edit_menu
        )

    def add_command(self, *args, **kwargs):
        return self._edit_menu.add_command(*args, **kwargs)

    def add_separator(self, *args, **kwargs):
        return self._edit_menu.add_separator(*args, **kwargs)

    def _make_menu(self):
        return tkinter.Menu(self._menu_bar, tearoff=0)
