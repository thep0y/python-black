#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:      thepoy
# @Email:       thepoy@163.com
# @File Name:   utils.py
# @Created At:  2022-02-04 10:51:04
# @Modified At: 2023-02-12 19:20:10
# @Modified By: thepoy

import sublime
import os

from typing import Optional, Union
from collections import namedtuple
from pathlib import Path
from .constants import PACKAGE_NAME, SETTINGS_FILE_NAME
from .log import child_logger
from .mode import Mode
from .lib.black.files import find_pyproject_toml
from .types import SublimeSettings

logger = child_logger(__name__)


ViewState = namedtuple("ViewState", ["row", "col", "vector"])


def show_error_panel(text: str):
    view = sublime.active_window().get_output_panel("black")
    view.set_read_only(False)
    view.run_command("black_output", {"text": text})
    view.set_read_only(True)
    sublime.active_window().run_command("show_panel", {"panel": "output.black"})


def find_current_file_path(view: sublime.View, filename: str) -> Optional[str]:
    window = view.window()
    if not window:
        return None

    filepath = window.extract_variables().get("file_path", None)
    if not filepath:
        return None

    return os.path.join(filepath, filename)


def find_root_path_of_current_file(view: sublime.View) -> Optional[Path]:
    current_file_name = view.file_name()
    if current_file_name:
        black_config_file = find_pyproject_toml((current_file_name,))
        if black_config_file:
            logger.debug("black found config file: %s", black_config_file)
            return Path(black_config_file)

    window = view.window()
    if not window:
        return None

    folders = window.folders()
    logger.debug(
        "black didn't find config file, falling back to first folder in project list: %s",
        folders,
    )
    if folders:
        return Path(folders[0]) / "pyproject.toml"

    return None


def get_project_setting_file(view: sublime.View) -> Optional[Path]:
    """find `pyproject.toml` in root path of current window

    Arguments:
        view {sublime.View} -- curennt sublime.View

    Returns:
        Optional[str] -- return black config file, or return None
    """
    project_settings_file = find_root_path_of_current_file(view)

    if not project_settings_file:
        return None

    if not project_settings_file.exists():
        return None

    logger.debug("found the project config file: %s", project_settings_file)

    return project_settings_file


def out(msg: str):
    return sublime.status_message(msg)


def save_state(view: sublime.View):
    # save cursor position
    row, col = view.rowcol(view.sel()[0].begin())
    # save viewport
    vector = view.text_to_layout(view.visible_region().begin())
    return ViewState(row, col, vector)


def restore_state(view: sublime.View, state: ViewState):
    # restore cursor position
    sel = view.sel()
    if len(sel) == 1 and sel[0].a == sel[0].b:
        point = view.text_point(state.row, state.col)
        sel.subtract(sel[0])
        sel.add(sublime.Region(point, point))
    # restore viewport
    # magic, next line doesn't work without it
    view.set_viewport_position((0.0, 0.0))
    view.set_viewport_position(state.vector)


def replace_text(
    edit: sublime.Edit, view: sublime.View, region: sublime.Region, text: str
):
    state = save_state(view)
    if region.b - region.a < view.size():
        lines = text.split("\n")
        if not lines[-1]:
            text = "\n".join(lines[:-1])
    view.replace(edit, region, text)
    restore_state(view, state)
    sublime.status_message("black: Formatted")


def get_package_settings() -> sublime.Settings:
    settings = sublime.load_settings(SETTINGS_FILE_NAME)
    logger.debug("sublime package settings: %s", settings.to_dict())
    return settings


def get_project_settings(view: sublime.View) -> SublimeSettings:
    window = view.window()
    if not window:
        return {}  # type: ignore

    project_settings: SublimeSettings = (
        (window.project_data() or {}).get("settings", {}).get(PACKAGE_NAME, {})  # type: ignore
    )
    logger.debug("sublime project settings: %s", project_settings)
    return project_settings


def get_mode():
    settings = get_package_settings()
    _mode: Union[str, bool] = settings.get("format_on_save")  # type: ignore
    if isinstance(_mode, str):
        mode = Mode(_mode)
    else:
        if _mode:
            mode = Mode.ON
        else:
            mode = Mode.OFF
    return mode


def set_mode(mode: Mode) -> None:
    logger.info("Setting mode to %r", mode)
    settings = sublime.load_settings(SETTINGS_FILE_NAME)
    settings.set("format_on_save", mode.value)
    sublime.save_settings(SETTINGS_FILE_NAME)
