import sublime
import sublime_plugin
from .constants import SETTINGS_FILE_NAME
from .utils import get_project_setting_file, black_format


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
        region, source, encoding = self.get_selection()
        if not isinstance(source, str) and hasattr(source, "decode"):
            source = source.decode(encoding)
        settings = sublime.load_settings(SETTINGS_FILE_NAME)
        command = settings.get("command")
        config_file = get_project_setting_file(self.view)
        filename = self.view.file_name()
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
