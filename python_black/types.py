#!/usr/bin/env python3
# -*- coding:utf-8 -*-

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
