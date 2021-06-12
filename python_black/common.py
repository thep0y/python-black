#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: common.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-11 23:45:55

from typing import Optional
import sublime
import os
import sys
import platform
import zipfile
import shutil
import hashlib

from .constants import PACKAGE_NAME, INSTALLED_PACKAGE_NAME


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


def get_package_path() -> str:
    packages_path = sublime.packages_path()
    python_black_path = os.path.join(packages_path, PACKAGE_NAME)
    return python_black_path


def append_third_lib(python_black_path: str):
    """添加项目中的依赖到系统环境中"""
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


def md5(filename: str) -> Optional[str]:
    if not os.path.isfile(filename):
        return None

    try:
        f = open(filename, 'rb')
    except:
        return None

    m = hashlib.md5()
    # 大文件处理
    while True:
        d = f.read(4096)
        if not d:
            break
        m.update(d)
    ret = m.hexdigest()
    f.close()
    return ret


def extract(python_black_path: str):
    # 检查当前是在 subime-package 包中执行的还是在 packags 目录中执行的
    current_path = os.path.abspath(os.path.dirname(__file__))
    installed_pkg_path = os.path.join(sublime.installed_packages_path(), INSTALLED_PACKAGE_NAME)
    md5_file = os.path.join(python_black_path, "md5")

    if current_path != installed_pkg_path:
        installed_pkg_md5 = md5(installed_pkg_path)
        if not installed_pkg_md5:
            raise Exception("Invalid md5")

        if os.path.exists(md5_file):
            with open(md5_file, "r") as f:
                saved_md5 = f.read()
                if installed_pkg_md5 == saved_md5:
                    # 如果之前保存的 md5 和现在的 md5 一样，说明没有更新，不需要执行下面的代码
                    # 只有在新安装或更新时才需要执行下面的代码
                    # 减少磁盘 IO
                    return

        if os.path.exists(python_black_path):
            try:
                shutil.rmtree(python_black_path)
            except:
                pass

        if not os.path.exists(python_black_path):
            os.mkdir(python_black_path)

        z = zipfile.ZipFile(installed_pkg_path, "r")
        for f in z.namelist():
            z.extract(f, python_black_path)
        z.close()

        # 将安装或更新的 sublime-package 的 md5 保存到 packages 中
        with open(md5_file, "w") as f:
            f.write(installed_pkg_md5)
