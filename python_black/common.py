#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: common.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-06 21:32:08

import sublime


def show_error_panel(text: str):
    view = sublime.active_window().get_output_panel("black")
    view.set_read_only(False)
    view.run_command("black_output", {"text": text})
    view.set_read_only(True)
    sublime.active_window().run_command("show_panel", {"panel": "output.black"})
