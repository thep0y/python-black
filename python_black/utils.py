#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: utils.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-09 21:35:15

import sublime
import os
import sys
import subprocess
import locale
import difflib


from io import StringIO
from typing import Any, List, Optional
from collections import namedtuple
from .constants import STATUS_MESSAGE_TIMEOUT

from .common import show_error_panel


ViewState = namedtuple("ViewState", ["row", "col", "vector"])


def create_diff(source: str, formatted: str, filepath: str) -> str:
    result = difflib.unified_diff(
        StringIO(source).readlines(), StringIO(formatted).readlines(), "original: %s" % filepath, "fixed: %s" % filepath
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
            cmd, env=system_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1
        )
    except FileNotFoundError:
        sublime.error_message("Unable to find the command, did you not install `black`?")


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
    sublime.set_timeout_async(lambda: sublime.status_message(""), STATUS_MESSAGE_TIMEOUT)


def find_current_file_path(view: sublime.View, filename: str) -> Optional[str]:
    window = view.window()
    filepath = window.extract_variables().get("file_path", None)
    if not filepath:
        return None
    return os.path.join(filepath, filename)


def find_root_path_of_current_file(view: sublime.View, filename: str) -> Optional[str]:
    window = view.window()
    # root path of current window
    folders = window.folders()
    if len(folders) > 0:
        return os.path.join(folders[0], filename)
    return None


def get_project_setting_file(view: sublime.View) -> Optional[str]:
    """find `pyproject.toml` in root path of current window

    Arguments:
        view {sublime.View} -- curennt sublime.View
    Returns:
        Optional[str] -- return black config file, or return None
    """
    project_settings_file = find_root_path_of_current_file(view, "pyproject.toml")
    if not project_settings_file:
        return None
    if not os.path.exists(project_settings_file):
        return None
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


def replace_text(edit: sublime.Edit, view: sublime.View, region: sublime.Region, text: str):
    state = save_state(view)
    if region.b - region.a < view.size():
        lines = text.split("\n")
        if not lines[-1]:
            text = "\n".join(lines[:-1])
    view.replace(edit, region, text)
    restore_state(view, state)
    sublime.status_message("black: formatted")


def format_source_file(
    edit: sublime.Edit, formatted: str, filepath: str, view: sublime.View, region: sublime.Region, encoding: str
):
    if view:
        replace_text(edit, view, region, formatted)
    else:
        with open(filepath, "w", encoding=encoding) as fd:
            fd.write(formatted)


def get_site_packages_path(command: str) -> List[str]:
    if sys.platform == "win32":
        # TODO: return a site-packages list
        # I am not using a windows system, and there is no
        # guarantee that the following line of code is correct
        return [os.path.join(command.split("Scripts")[0], "Lib", "site-packages")]
    else:
        lib_path = os.path.join(command.replace("bin/black", ""), "lib")
        return [
            os.path.join(lib_path, i, "site-packages") for i in os.listdir(lib_path) if i.lower().startswith("python")
        ]


def black_command_is_absolute_path(command: str) -> bool:
    if not os.path.exists(command):
        return False
    return os.path.isabs(command)


def format_by_popen(command: str, source: str, view: sublime.View):
    from .constants import CODE, CONFIG

    config_file = get_project_setting_file(view)

    if config_file:
        cmd_result = popen([command, CODE, source, CONFIG, config_file])
    else:
        cmd_result = popen([command, CODE, source])
    out, err = cmd_result.communicate()
    if out:
        # Remove the last `\n`
        out = out[:-1]
        return out
    show_error_panel("python-black:\n" + err)


def format_by_import_black_package(source: str, filepath: str) -> Optional[str]:
    from .black import really_format

    formatted = really_format(source, src=(filepath,))
    if not formatted:
        # When formatting the selection, an error may be
        # reported due to indentation issues, but this is
        # a issue with `black` and I may fix it in the future.
        show_error_panel("python-black:\nformatted fail")
        return
    return formatted


def black_format(
    source: str,
    filepath: str,
    region: sublime.Region,
    encoding: str,
    edit: sublime.Edit,
    view: sublime.View,
    # preview: bool = False,
):
    sublime.status_message("black: formatting...")

    formatted = format_by_import_black_package(source, filepath)

    if formatted:
        format_source_file(edit, formatted, filepath, view, region, encoding)
