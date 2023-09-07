#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Author:      thepoy
# @Email:       thepoy@163.com
# @File Name:   black.pyi
# @Created At:  2023-02-12 18:49:31
# @Modified At: 2023-02-12 19:12:40
# @Modified By: thepoy

from typing import TypedDict, List
from .mode import Mode


class BlackConfig(TypedDict):
    target_version: List[str]
    line_length: int
    is_pyi: bool
    skip_source_first_line: bool
    skip_string_normalization: bool
    skip_magic_trailing_comma: bool
    include: str


class SublimeSettings(TypedDict):
    format_on_save: Mode
    options: BlackConfig
