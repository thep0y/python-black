#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: utils.py
# @Created:   2022-02-04 10:51:04
# @Modified:  2022-11-01 21:12:39

import sublime
import os
import sys
import subprocess
import locale
import difflib

from io import StringIO
from typing import Any, Dict, List, Optional, Union
from collections import namedtuple
from pathlib import Path
from .constants import PACKAGE_NAME, SETTINGS_FILE_NAME, STATUS_MESSAGE_TIMEOUT
from .log import child_logger
from .mode import Mode
from .lib.black.files import find_pyproject_toml

logger = child_logger(__name__)


ViewState = namedtuple("ViewState", ["row", "col", "vector"])


def show_error_panel(text: str):
    view = sublime.active_window().get_output_panel("black")
    view.set_read_only(False)
    view.run_command("black_output", {"text": text})
    view.set_read_only(True)
    sublime.active_window().run_command("show_panel", {"panel": "output.black"})


def create_diff(source: str, formatted: str, filepath: str) -> str:
    result = difflib.unified_diff(
        StringIO(source).readlines(),
        StringIO(formatted).readlines(),
        "original: %s" % filepath,
        "fixed: %s" % filepath,
    )
    # fix issue with join two last lines
    lines = [item for item in result]
    if len(lines) >= 4 and lines[-2][-1] != "\n":
        lines[-2] += "\n"
    return "".join(lines) if len(lines) >= 3 else ""


def system_env():
    # modifying the locale is necessary to keep the click library happy on OSX
    env = os.environ.copy()
    if locale.getdefaultlocale() == (None, None):
        if sublime.platform() == "osx":
            env["LC_CTYPE"] = "UTF-8"
    return env


def popen(cmd: List[Any]):
    try:
        return subprocess.Popen(
            cmd,
            env=system_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )
    except FileNotFoundError:
        sublime.error_message(
            "Unable to find the command, did you not install `black`?"
        )


def new_view(encoding: str, text: str):
    view = sublime.active_window().new_file()
    view.set_encoding(encoding)
    view.set_syntax_file("Packages/Diff/Diff.tmLanguage")
    view.run_command("black_output", {"text": text})
    view.set_scratch(True)


def show_result(result):
    diffs = []
    not_fixed = ""
    has_changes = False
    # merge diffs.
    for command_result in result:
        if "diff" in command_result:
            diffs.append(command_result["diff"])
        not_fixed += command_result["not_fixed"]
        has_changes = has_changes or command_result.get("has_changes")
    # show status message.
    message = "python-black: No issues to fix."
    if has_changes:
        message = "python-black: Issues were fixed."
    sublime.status_message(message)
    (not_fixed)
    # show diff.
    if diffs:
        new_view("utf-8", "\n".join(diffs))
    sublime.set_timeout_async(
        lambda: sublime.status_message(""), STATUS_MESSAGE_TIMEOUT
    )


def find_current_file_path(view: sublime.View, filename: str) -> Optional[str]:
    window = view.window()
    filepath = window.extract_variables().get("file_path", None)  # type: ignore
    if not filepath:
        return None
    return os.path.join(filepath, filename)


def find_root_path_of_current_file(view: sublime.View) -> Optional[Path]:
    current_file_name = view.file_name()
    if current_file_name:
        black_config_file = find_pyproject_toml((current_file_name,))
        if black_config_file:
            logger.debug("black found config file: %s", black_config_file)
            return black_config_file

    folders = view.window().folders()  # type: ignore
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

    if not os.path.exists(project_settings_file):
        return None

    logger.debug("found the project config file: %s", project_settings_file)

    return project_settings_file


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


def get_site_packages_path(command: str) -> List[str]:
    if sys.platform == "win32":
        return [os.path.join(command.split("Scripts")[0], "Lib", "site-packages")]
    else:
        lib_path = os.path.join(command.replace("bin/black", ""), "lib")
        return [
            os.path.join(lib_path, i, "site-packages")
            for i in os.listdir(lib_path)
            if i.lower().startswith("python")
        ]


def black_command_is_absolute_path(command: str) -> bool:
    if not os.path.exists(command):
        return False
    return os.path.isabs(command)


def out(msg: str):
    return sublime.status_message(msg)


def get_package_settings() -> sublime.Settings:
    settings = sublime.load_settings(SETTINGS_FILE_NAME)
    logger.debug("sublime package settings: %s", settings.to_dict())
    return settings


def get_project_settings(view: sublime.View) -> Dict[str, Any]:
    window = view.window()
    if not window:
        return {}

    project_settings: Dict[str, Dict[str, Any]] = (
        (window.project_data() or {}).get("settings", {}).get(PACKAGE_NAME, {})
    )
    logger.debug("sublime project settings: %s", project_settings)
    return project_settings


def get_mode():
    settings = get_package_settings()
    _mode: Union[str, bool] = settings.get("format_on_save")
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
