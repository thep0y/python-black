#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: utils.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-02 21:10:12

import os
import sublime

from typing import Optional


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
