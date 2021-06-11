#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: commands.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-11 23:37:37

import sublime
import sublime_plugin


from os import path
from typing import List

from .python_black.constants import SETTINGS_FILE_NAME, CONFIGURATION_FILENAME, CONFIGURATION_CONTENTS
from .python_black.utils import black_format


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
        if filename:
            black_format(source=source, filepath=filename, region=region, encoding=encoding, edit=edit, view=self.view)


class BlackAllFilesCommand(sublime_plugin.TextCommand):
    # TODO 格式化项目中所有 py 文件
    # 应该传入文件路径，而不是文件内容
    # 这里还用 TextCommand ？还是换 WindowCommand？
    def run(self, edit):
        sublime.error_message("没写完")


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


class BlackOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        self.view.insert(edit, 0, text)
        self.view.end_edit(edit)

    def is_visible(self, *args):
        return False


def plugin_loaded():
    from .python_black.common import get_package_path, extract, append_third_lib

    package_path = get_package_path()
    extract(package_path)
    append_third_lib(package_path)
    sublime.status_message("python-black: Third-party dependencies loaded")
