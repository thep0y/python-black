#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: log.py
# @Created:   2022-10-29 16:21:52
# @Modified:  2022-10-29 17:45:47

import os
import logging
import sublime

from typing import Dict, Optional, Literal, Tuple
from datetime import datetime
from .constants import LOGGER_NAME, TIME_FORMAT_WITHOUT_DATE
from .color import DisplayStyle, Style

ds = DisplayStyle()

_style = Literal["%", "{", "$"]


class BlackLogger(logging.Logger):
    pass


class Formatter(logging.Formatter):
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: _style = "%",
        print_position=True,
        to_file=False,
    ):
        self.default_color = "{0}"
        self.print_position = print_position

        self.level_config: Dict[str, Tuple[str, Style]] = {
            "DEBUG": ("DEB", ds.fc.purple),
            "INFO": ("INF", ds.fc.green),
            "WARN": ("WAR", ds.fc.yellow),
            "WARNING": ("WAR", ds.fc.yellow),
            "ERROR": ("ERR", ds.fc.light_red),
            "FATAL": ("FAT", ds.fc.red),
            "CRITICAL": ("FAT", ds.fc.red),
        }

        self.to_file = to_file

        super().__init__(fmt, datefmt, style)

    def __level(self, levelname: str):
        level = self.level_config[levelname]

        if self.to_file:
            return "%s%s%s " % (
                ds.format_with_one_style("[", ds.fc.light_gray),
                ds.format_with_one_style(level[0], level[1]),
                ds.format_with_one_style("]", ds.fc.light_gray),
            )

        return "[%s] " % level[0]

    def __time(self, record):
        assert isinstance(self.datefmt, str)

        t = datetime.fromtimestamp(record.created)
        s = (
            t.strftime(self.datefmt)[:-3]
            if self.datefmt == TIME_FORMAT_WITHOUT_DATE
            else t.strftime(self.datefmt)
        )

        if self.to_file:
            return ds.format_with_one_style(s, ds.fc.dark_gray) + " "

        return s + " "

    def __name(self, record):
        if self.to_file:
            return (
                ""
                if record.name == "root"
                else ds.format_with_one_style(record.name, ds.fc.cyan)
            )

        return "" if record.name == "root" else f"{record.name}"

    def __position(self, record: logging.LogRecord):
        if not self.print_position:
            return ""

        if record.levelname in ["INFO"]:
            return ""

        if self.to_file:
            return (
                ds.format_with_multiple_styles(
                    f":{record.lineno}", ds.fc.light_yellow, ds.mode.bold
                )
                + " "
            )

        return f":{record.lineno} "

    @property
    def __connector(self):
        if self.to_file:
            return ds.format_with_one_style("-", ds.fc.light_cyan) + " "

        return "- "

    def format(self, record: logging.LogRecord):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        msg = record.msg % record.args if record.args else record.msg

        return (
            self.__level(record.levelname)
            + self.__time(record)
            + self.__name(record)
            + self.__position(record)
            + self.__connector
            + msg
        )


def log_level() -> int:
    """Get the log level.
    Returns `DEBUG` in debug mode, `INFO` otherwise.

    Returns:
        int: log level
    """
    current_path = os.path.abspath(os.path.dirname(__file__))
    return (
        logging.INFO
        if current_path.startswith(sublime.installed_packages_path())
        else logging.DEBUG
    )


def stream_handler():
    fmt = Formatter(datefmt=TIME_FORMAT_WITHOUT_DATE, print_position=True)
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)

    return handler


def file_handler():
    fmt = Formatter(datefmt=TIME_FORMAT_WITHOUT_DATE, print_position=True, to_file=True)

    packages_path: str = sublime.packages_path()
    sublime_config_path = os.path.dirname(packages_path)
    log_dir_path = os.path.join(sublime_config_path, "Log")

    if not os.path.exists(log_dir_path):
        os.mkdir(log_dir_path)

    handler = logging.FileHandler(
        filename=os.path.join(log_dir_path, f"{LOGGER_NAME}.log"),
        mode="w",
        encoding="utf-8",
    )
    handler.setFormatter(fmt)

    return handler


def get_logger():
    """Get the root logger of the package.

    Use a custom Formatter to create a logger
    that is only valid for this package.

    Since the sublime console does not support color printing,
    for better debugging, I save the color log to a file.

    When debugging, you can read the color log through
    `tail -f` (unix-like) or `Get-Content -Wait -Path` (Windows).

    Returns:
        Logger: the instance of `logging.Logger`
    """
    logger = BlackLogger(LOGGER_NAME)

    level = log_level()

    if level == logging.DEBUG:
        logger.addHandler(stream_handler())

    logger.addHandler(file_handler())

    logger.setLevel(level)

    return logger


__logger = get_logger()


def child_logger(name: str) -> logging.Logger:
    """Get a new child logger with `name`.
    Args:
        name (str): the name of child logger
    Returns:
        Logger: the instance of `logging.Logger`
    """
    log = __logger.getChild(name.replace(f"{LOGGER_NAME}.", ""))
    log.setLevel(__logger.level)
    log.handlers = __logger.handlers

    return log
