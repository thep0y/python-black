#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: constants.py
# @Created: 2021-03-27 09:55:27
# @Modified: 2021-06-11 23:45:03

PACKAGE_NAME = "python-black"
INSTALLED_PACKAGE_NAME = f"{PACKAGE_NAME}.sublime-package"
SETTINGS_FILE_NAME = "%s.sublime-settings" % PACKAGE_NAME

WORKER_TIMEOUT = 0
WORKER_START_TIMEOUT = 100
STATUS_MESSAGE_TIMEOUT = 3000

COMMAND = "black"
CODE = "-c"
CONFIG = "--config"

TIMEOUT = 0
FORMAT_TIMEOUT = 100
STATUS_MESSAGE_TIMEOUT = 3000

CONFIGURATION_FILENAME = "pyproject.toml"
CONFIGURATION_CONTENTS = """[tool.black]
line-length = 120
target-version = ['py38']
include = '\\.pyi?\\$'
extend-exclude = '''
# A regex preceded with ^/ will apply only to files and directories
# in the root of the project.
^/foo.py  # exclude a file named foo.py in the root of the project (in addition to the defaults)
'''"""
