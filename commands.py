#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: commands.py
# @Created:   2022-02-04 10:51:04
# @Modified:  2023-02-08 13:31:30

import sublime
import sublime_plugin

from os import path
from typing import Any, Dict, List, Union

from .python_black.constants import (
    SETTINGS_FILE_NAME,
    CONFIGURATION_FILENAME,
    CONFIGURATION_CONTENTS,
)
from .python_black.black import black_format
from .python_black.mode import Mode
from .python_black.log import child_logger
from .python_black.utils import get_mode, set_mode
from .python_black.lib.black import __version__ as black_version
from .python_black.lib.pathspec import __version__ as pathspec_version
from .python_black.lib.platformdirs import __version__ as platformdirs_version
from .python_black.lib.tomli import __version__ as tomli_version
from .python_black.lib.appdirs import __version__ as appdirs_version

logger = child_logger(__name__)

logger.info(
    "versions: black=%s, pathspec=%s, platformdirs=%s, tomli=%s, appdirs=%s",
    black_version,
    pathspec_version,
    platformdirs_version,
    tomli_version,
    appdirs_version,
)


class BlackCommand(sublime_plugin.TextCommand):
    def is_visible(self, *args):
        region = self.view.sel()[0]
        return self.view.match_selector(region.b, "source.python")

    def get_source(self, use_selection: bool):
        region = self.view.sel()[0]
        # select the whole view if there is no selected region
        if region.a == region.b or not use_selection:
            region = sublime.Region(0, self.view.size())
        return region, self.view.substr(region), self.view.encoding()

    def run(self, edit: sublime.Edit, use_selection=True, smart_mode=False):
        logger.info("use smart mode: %s", smart_mode)

        filename = self.view.file_name() or ""

        if self.view.settings().get("syntax").lower().find("python") == -1:
            sublime.status_message(
                f"black: The current file is not a python script: {filename}"
            )
            return

        region, source, encoding = self.get_source(use_selection)

        if not isinstance(source, str) and hasattr(source, "decode"):
            source = source.decode(encoding)

        black_format(
            source=source,
            filepath=filename,
            region=region,
            encoding=encoding,
            edit=edit,
            view=self.view,
            smart_mode=smart_mode,
        )


class BlackCreateConfiguration(sublime_plugin.WindowCommand):
    def run(self) -> None:
        folders = self.window.folders()
        if len(folders) == 0:
            sublime.message_dialog(
                "No folders found in the window. Please add a folder first."
            )
        elif len(folders) == 1:
            self._create_configuration(folders[0])
        else:
            self.window.show_quick_panel(
                folders,
                lambda index: self._on_selected(folders, index),
                placeholder="Select a folder to create the configuration file in",
            )

    def _on_selected(self, folders: List[str], index: int) -> None:
        if index > -1:
            self._create_configuration(folders[index])

    def _create_configuration(self, folder_path: str) -> None:
        config_path = path.join(folder_path, CONFIGURATION_FILENAME)
        new_view = self.window.open_file(config_path)
        if not path.isfile(config_path):
            self._poll_view_until_loaded(new_view)

    def _poll_view_until_loaded(self, view: sublime.View, attempt: int = 1) -> None:
        if attempt > 10:
            return
        if view.is_loading():
            sublime.set_timeout(
                lambda: self._poll_view_until_loaded(view, attempt + 1), 100
            )
        else:
            self._on_view_loaded(view)

    def _on_view_loaded(self, view: sublime.View) -> None:
        view.run_command("insert_snippet", {"contents": CONFIGURATION_CONTENTS})


class AutoFormatOnSave(sublime_plugin.EventListener):
    def format_on_save_mode(self, view: sublime.View) -> Mode:
        settings = sublime.load_settings(SETTINGS_FILE_NAME)
        _mode: Union[str, bool] = settings.get("format_on_save", "off")  # type: ignore

        window = view.window()
        if window:
            # fmt: off
            project_settings: Dict[str, Dict[str, Any]] = (
                window.project_data() or {}
            ).get("settings", {}) # type: ignore
            # fmt: on
            _mode = project_settings.get("python-black", {}).get(
                "format_on_save", _mode
            )

        if isinstance(_mode, str):
            mode = Mode(_mode)
        else:
            mode = Mode.ON if _mode else Mode.OFF

        return mode

    def on_pre_save(self, view: sublime.View):
        mode = self.format_on_save_mode(view)

        if mode == Mode.ON:
            view.run_command("black", {"use_selection": False})
            sublime.status_message("black: Document has been automatically formatted")
        elif mode == Mode.SMART:
            view.run_command("black", {"use_selection": False, "smart_mode": True})


class BlackOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        self.view.insert(edit, 0, text)
        self.view.end_edit(edit)

    def is_visible(self, *args):
        return False


class ToggleFormatOnSaveCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        mode = get_mode()
        if mode == Mode.SMART:
            sublime.error_message("black: Unable to toggle in `smart` mode")
        else:
            new_mode = Mode.ON if mode == Mode.OFF else Mode.OFF
            set_mode(new_mode)

    def description(self):
        return "Format On Save (Global)"


class SetFormatOnSaveToSmartCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        set_mode(Mode.SMART)

    def is_checked(self):
        mode = get_mode()
        return mode == Mode.SMART

    def description(self):
        return 'Set "Format On Save" to "Smart"'


class SetFormatOnSaveToOnCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        set_mode(Mode.ON)

    def is_checked(self):
        mode = get_mode()
        return mode == Mode.ON

    def description(self):
        return 'Set "Format On Save" to "On"'


class SetFormatOnSaveToOffCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        set_mode(Mode.OFF)

    def is_checked(self):
        mode = get_mode()
        return mode == Mode.OFF

    def description(self):
        return 'Set "Format On Save" to "Off"'
