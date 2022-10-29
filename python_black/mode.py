#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: mode.py
# @Created:   2022-10-29 15:29:53
# @Modified:  2022-10-29 15:32:46

from enum import Enum


class Mode(Enum):
    OFF = False
    ON = True
    SMART = "smart"
