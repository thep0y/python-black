import os

import sublime
import sublime_plugin

from .constants import SETTINGS_FILE_NAME
from .utils import get_project_setting_file


class BlackCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        current_file_path = self.view.file_name()
        if not current_file_path.endswith(".py"):
            return

        settings = sublime.load_settings(SETTINGS_FILE_NAME)

        command = settings.get("command")

        # TODO: 支持更多 black 选项
        max_line_length = settings.get("max-line-length")
        target_version = settings.get("target-version")

        result = os.popen("%s --version" % command).read()
        if not result.startswith("black, version "):
            raise Exception("command [ %s ] not found. Have you installed `black`?" % command)

        black_config_file = get_project_setting_file(self.view)
        if black_config_file:
            cmd = f"{command} --config {black_config_file} {current_file_path}"
        else:
            if target_version:
                cmd = f"{command} --line-length {max_line_length} --target-version {target_version[0]} {current_file_path}"
            else:
                cmd = f"{command} --line-length {max_line_length} {current_file_path}"

        # TODO: 格式化成功的话，sublime 会重新加载当前文件，导致不会有任何输出
        os.popen(cmd)
