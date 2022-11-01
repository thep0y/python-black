#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author:    thepoy
# @Email:     thepoy@163.com
# @File Name: black.py
# @Created:   2022-02-04 10:51:04
# @Modified:  2022-11-01 20:49:14

import sublime
import sys

from pathlib import Path
from typing import Optional, Any, Dict, Tuple, List

from .lib.black import format_str
from .lib.black.files import parse_pyproject_toml
from .lib.black.mode import Mode, TargetVersion
from .lib.black.const import DEFAULT_LINE_LENGTH, DEFAULT_INCLUDES
from .utils import get_project_setting_file, replace_text, out
from .log import child_logger


logger = child_logger(__name__)


def target_version_option_callback(v: Tuple[str, ...]) -> List[TargetVersion]:
    return [TargetVersion[val.upper()] for val in v]


def find_global_config_file() -> Optional[Path]:
    HOME = Path.home()

    if sys.platform == "win32":
        config_file = HOME / ".black"
    else:
        config_file = HOME / ".config" / "black"

    config_file.is_file()
    if config_file.exists() and config_file.is_file():
        return config_file

    return None


def find_config_file(view: sublime.View, smart_mode: bool):
    config_file = get_project_setting_file(view)
    if not config_file:
        # only use `pyproject.toml` in smart mode
        if smart_mode:
            return None

        # find global config file
        config_file = find_global_config_file()
        if not config_file:
            return None

    return config_file


def read_pyproject_toml(
    config_file: Path,
    default_config: Dict[str, Any],
    smart_mode: bool,
) -> Tuple[Dict[str, Any], Optional[Path]]:
    """Inject Black configuration from "pyproject.toml" into defaults config.

    Returns the configuration dict and config file path to
    a successfully found and read configuration file, None otherwise.

    Args:
        config_file (Optional[str]): Description
        default_config (Optional[Dict[str, Any]]): Description
        src (Tuple[str, ...]): Description

    Returns:
        Tuple[Optional[dict], Optional[str]]: config and config file
    """
    try:
        config = parse_pyproject_toml(str(config_file))
    except (OSError, ValueError, FileNotFoundError) as e:
        raise Exception(f"Error reading configuration file: {e}")

    logger.debug("project config: %s", config)

    if smart_mode and not config:
        return {}, None

    logger.debug("parsed config: %s", config)

    if not config:
        return default_config, None

    config = {
        k: str(v) if not isinstance(v, (list, dict)) else v for k, v in config.items()
    }

    target_version = config.get("target_version")
    if target_version is not None and not isinstance(target_version, list):
        raise AttributeError("target-version: Config key target-version must be a list")

    default_map: Dict[str, Any] = {}
    if default_config:
        default_map.update(default_config)

    default_map.update(config)

    logger.info("used config: %s", default_map)

    return default_map, config_file


def really_format(
    code: str,
    config_file: Optional[Path],
    smart_mode: bool,
) -> Optional[str]:
    """
    Directly call the format function of the `black`
    package to complete the formatting of the code.

    Args:
        code (str): The code to be formatted
        src (Tuple[str, ...]): Files path to be formatted.
            Currently only one file can be formatted, so only one path can be passed in
        config_file (Optional[str]): Configuration file to be used (default: {None})

    Returns:
        Optional[str]: Formatted code
    """
    default_config: Dict[str, Any] = {
        "line_length": DEFAULT_LINE_LENGTH,
        "skip_source_first_line": False,
        "skip_string_normalization": False,
        "skip_magic_trailing_comma": False,
        "experimental_string_processing": False,
        "include": DEFAULT_INCLUDES,
    }

    if config_file:
        default_config, config_file = read_pyproject_toml(
            config_file, default_config, smart_mode
        )

    if not default_config:
        logger.info(
            "smart mode is in use, but the black section is not found in the config file"
        )
        sublime.status_message("black: Black section is not found")

        return None

    if config_file:
        out(f"Using configuration from {config_file}.")
    else:
        out("No configuration file found, use the default configuration")

    versions = set()
    target_version_in_config_file = default_config.get("target_version")
    if target_version_in_config_file:
        target_version = target_version_option_callback(tuple(target_version_in_config_file))  # type: ignore
        if target_version:
            versions = set(target_version)

    mode = Mode(
        target_versions=versions,
        line_length=int(default_config["line_length"]),
        is_pyi=False,
        skip_source_first_line=default_config["skip_source_first_line"],
        string_normalization=not default_config["skip_string_normalization"],
        magic_trailing_comma=not default_config["skip_magic_trailing_comma"],
        experimental_string_processing=default_config["experimental_string_processing"],
    )

    if code:
        formatted = format_str(code, mode=mode)

        return formatted


def format_by_import_black_package(
    view: sublime.View, source: str, smart_mode: bool
) -> Optional[str]:
    config_file = find_config_file(view, smart_mode)

    logger.debug("found the config file: %s", config_file)

    if smart_mode and not config_file:
        logger.info("smart mode is in use, but the project config file is not found")
        sublime.status_message("black: Project config file is not found")

        return None

    formatted = really_format(source, config_file, smart_mode=smart_mode)
    if not formatted:
        # When formatting the selection, an error may be
        # reported due to indentation issues, but this is
        # a issue with `black` and I may fix it in the future.
        if not smart_mode:
            sublime.status_message("black: Format failed")

        return

    return formatted


def black_format(
    source: str,
    filepath: str,
    region: sublime.Region,
    encoding: str,
    edit: sublime.Edit,
    view: sublime.View,
    smart_mode: bool,
    # preview: bool = False,
):
    sublime.status_message("black: Formatting...")

    formatted = format_by_import_black_package(view, source, smart_mode)

    if formatted:
        format_source_file(edit, formatted, filepath, view, region, encoding)


def format_source_file(
    edit: sublime.Edit,
    formatted: str,
    filepath: str,
    view: sublime.View,
    region: sublime.Region,
    encoding: str,
):
    if view:
        replace_text(edit, view, region, formatted)
    else:
        with open(filepath, "w", encoding=encoding) as fd:
            fd.write(formatted)
