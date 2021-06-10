#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: common.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-09 21:36:04

import sublime
import os
import sys
import platform

from .constants import PACKAGE_NAME


def show_error_panel(text: str):
    view = sublime.active_window().get_output_panel("black")
    view.set_read_only(False)
    view.run_command("black_output", {"text": text})
    view.set_read_only(True)
    sublime.active_window().run_command("show_panel", {"panel": "output.black"})


def get_system_info() -> str:
    system_name = platform.system().lower()
    # macOS 只用64位
    if system_name == "darwin":
        return f"{system_name}_x64"
    architecture = platform.architecture()[0][:2]
    return f"{system_name}_x{architecture}"


def append_third_lib():
    """添加项目中的依赖到系统环境中"""
    packages_path = sublime.packages_path()
    python_black_path = os.path.join(packages_path, PACKAGE_NAME)
    third_libs_path = os.path.join(python_black_path, "lib")

    # 针对不同系统导入不同包
    system_info = get_system_info()

    system_lib = os.path.join(third_libs_path, system_info)
    common_lib = os.path.join(third_libs_path, "common")

    if system_lib not in sys.path:
        # 添加对应的系统库
        sys.path.append(system_lib)

    if common_lib not in sys.path:
        # 添加通用库，没有引用二进制库的纯 python 库放到通用库中
        sys.path.append(common_lib)
