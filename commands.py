#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: commands.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-05 23:35:54

import sublime
import sublime_plugin


from os import path
from typing import List

from .python_black.constants import SETTINGS_FILE_NAME, CONFIGURATION_FILENAME, CONFIGURATION_CONTENTS
from .python_black.utils import get_project_setting_file, black_format


class BlackCommand(sublime_plugin.TextCommand):
    def is_visible(self, *args):
        return True

    def get_selection(self):
        region = self.view.sel()[0]
        # select the whole view if there is no selected region
        if region.a == region.b:
            region = sublime.Region(0, self.view.size())
        return region, self.view.substr(region), self.view.encoding()

    def run(self, edit: sublime.Edit):
        filename = self.view.file_name()
        if filename and not filename.endswith(".py"):
            sublime.status_message(f"black: The current file is not a python script file: {filename}")
            return
        if not filename:
            sublime.error_message("black: Unrecognized file name")
            return

        region, source, encoding = self.get_selection()
        if not isinstance(source, str) and hasattr(source, "decode"):
            source = source.decode(encoding)
        settings = sublime.load_settings(SETTINGS_FILE_NAME)
        command = settings.get("command")
        config_file = get_project_setting_file(self.view)
        if filename:
            # TODO: 异步格式化时会有 edit 不能在函数外部使用的错误，如何解决？
            # fn = filename  # 为了消除 pyright 的错误提示，这行代码本身是多余的
            # # set_timeout_async 方法会让 edit.edit_token 归零，在调用 view.replace 时，edit.edit_token 却不能为零
            # sublime.set_timeout_async(
            #     lambda: format(source, fn, region, encoding, edit, self.view, config_file=config_file),
            #     FORMAT_TIMEOUT,
            # )

            # 同步格式化
            black_format(command, source, filename, region, encoding, edit, self.view, config_file=config_file)


class BlackCreateConfiguration(sublime_plugin.WindowCommand):
    def run(self) -> None:
        folders = self.window.folders()
        if len(folders) == 0:
            sublime.message_dialog("No folders found in the window. Please add a folder first.")
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
            sublime.set_timeout(lambda: self._poll_view_until_loaded(view, attempt + 1), 100)
        else:
            self._on_view_loaded(view)

    def _on_view_loaded(self, view: sublime.View) -> None:
        view.run_command("insert_snippet", {"contents": CONFIGURATION_CONTENTS})


class AutoFormatOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view: sublime.View):
        settings = sublime.load_settings(SETTINGS_FILE_NAME)
        status = settings.get("format_on_save")
        if status:
            view.run_command("black")
            sublime.status_message("black: Document is automatically formatted")
