#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sublime
import sys

from pathlib import Path
from typing import Optional, Tuple, List

from .lib import tomli as tomllib
from .lib.black import format_str
from .lib.black.files import infer_target_version
from .lib.black.mode import Mode, TargetVersion
from .lib.black.const import DEFAULT_LINE_LENGTH, DEFAULT_INCLUDES
from .types import BlackConfig, SublimeSettings
from .utils import get_project_setting_file, replace_text, out
from .log import child_logger


logger = child_logger(__name__)


def target_version_option_callback(v: List[str]) -> List[TargetVersion]:
    return [TargetVersion[val.upper()] for val in v]


def find_global_config_file() -> Optional[Path]:
    HOME = Path.home()

    if sys.platform == "win32":
        config_file = HOME / ".black"
    else:
        config_file = HOME / ".config" / "black"

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
    default_config: BlackConfig,
    smart_mode: bool,
) -> Tuple[Optional[BlackConfig], Optional[Path]]:
    """Inject Black configuration from "pyproject.toml" into defaults config.

    Returns the configuration dict and config file path to
    a successfully found and read configuration file, None otherwise.

    Args:
        config_file (Optional[str]): Configuration file to be used
        default_config (Optional[BlackConfig]): Default configuration
        smart_mode (bool): Whether to use smart mode

    Returns:
        Tuple[Optional[BlackConfig], Optional[str]]: config and config file
    """
    with config_file.open("rb") as f:
        pyproject_toml = tomllib.load(f)
    config = pyproject_toml.get("tool", {}).get("black", {})
    config = {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}

    logger.debug("project config: %s", config)

    if smart_mode and not config:
        return None, None

    logger.debug("parsed config: %s", config)

    if not config:
        return default_config, None

    if "target_version" not in config:
        inferred_target_version = infer_target_version(pyproject_toml)
        if inferred_target_version is not None:
            config["target_version"] = [v.name.lower() for v in inferred_target_version]
        logger.debug("inferred target version: %s", inferred_target_version)
    else:
        target_version = config["target_version"]
        if target_version is not None and not isinstance(target_version, list):
            raise TypeError("target-version: Config key target-version must be a list")

    exclude = config.get("exclude")
    if exclude is not None and not isinstance(exclude, str):
        raise TypeError("exclude: Config key exclude must be a string")

    extend_exclude = config.get("extend_exclude")
    if extend_exclude is not None and not isinstance(extend_exclude, str):
        raise TypeError("extend-exclude: Config key extend-exclude must be a string")

    default_map: BlackConfig = {}  # type: ignore
    if default_config:
        default_map.update(default_config)

    default_map.update(config)  # type: ignore

    logger.debug("configuration after applying `pyproject.toml`: %s", default_map)

    return default_map, config_file


def update_config(default_config: BlackConfig, settings: SublimeSettings):
    default_config.update(
        {
            k: v  # type: ignore
            for k, v in settings.get("options", {}).items()
            if k in default_config
            and any([(not isinstance(v, bool) and v), isinstance(v, bool)])
        }
    )


def black_format_str(
    code: str,
    config_file: Optional[Path],
    smart_mode: bool,
    package_settings: Optional[SublimeSettings],
    project_settings: Optional[SublimeSettings],
) -> Optional[str]:
    """
    Directly call the format function of the `black`
    package to complete the formatting of the code.

    Args:
        code (str): The code to be formatted
        src (Tuple[str, ...]): Files path to be formatted.
            Currently only one file can be formatted, so only one path can be passed in
        config_file (Optional[str]): Configuration file to be used (default: {None})
        package_settings (Optional[Dict[str, Any]]): Package settings
        project_settings (Optional[Dict[str, Any]]): Project settings

    Returns:
        Optional[str]: Formatted code
    """
    default_config: Optional[BlackConfig] = {
        "target_version": [],
        "line_length": DEFAULT_LINE_LENGTH,
        "is_pyi": False,
        "preview": False,
        "skip_source_first_line": False,
        "skip_string_normalization": False,
        "skip_magic_trailing_comma": False,
        "include": DEFAULT_INCLUDES,
    }

    # NOTE: Update default config from package settings.
    if package_settings and isinstance(package_settings, dict):
        update_config(default_config, package_settings)
        logger.debug(
            "configuration after applying `Sublime Package User Settings`: ",
            default_config,
        )

    if config_file:
        default_config, config_file = read_pyproject_toml(
            config_file, default_config, smart_mode
        )

    if not default_config:
        logger.info(
            "Using smart mode, but no [black] section found in config file, "
            "so no Python files in the current project will be formatted."
        )
        sublime.status_message("black: Black section is not found")

        return None

    if config_file:
        out(f"Using configuration from {config_file}.")
    else:
        out("No configuration file found, use the default configuration")

    # NOTE: Update default config from project settings.
    if project_settings and isinstance(project_settings, dict):
        update_config(default_config, project_settings)
        logger.debug(
            "configuration after applying `Sublime Project Settings`: %s",
            default_config,
        )

    versions = set()
    target_version_in_config_file = default_config.get("target_version")
    if target_version_in_config_file:
        target_version = target_version_option_callback(target_version_in_config_file)
        if target_version:
            versions = set(target_version)

    logger.info("configuration used: %s", default_config)

    mode = Mode(
        target_versions=versions,
        line_length=default_config["line_length"],
        is_pyi=default_config["is_pyi"],
        preview=default_config["preview"],
        skip_source_first_line=default_config["skip_source_first_line"],
        string_normalization=not default_config["skip_string_normalization"],
        magic_trailing_comma=not default_config["skip_magic_trailing_comma"],
    )

    if code:
        formatted = format_str(code, mode=mode)

        return formatted


def format_by_import_black_package(
    view: sublime.View,
    source: str,
    smart_mode: bool,
    package_settings: Optional[SublimeSettings],
    project_settings: Optional[SublimeSettings],
) -> Optional[str]:
    config_file = find_config_file(view, smart_mode)

    logger.info("configuration file used: %s", config_file)

    if smart_mode and not config_file:
        logger.info("smart mode is in use, but the project config file is not found")
        sublime.status_message("black: Project config file is not found")

        return

    # NOTE: Ignore package and project settings if smart mode is enabled.
    if smart_mode:
        package_settings, project_settings = None, None

    formatted = black_format_str(
        source, config_file, smart_mode, package_settings, project_settings
    )
    if not formatted:
        # When formatting the selection, an error may be
        # reported due to indentation issues, but this is
        # a issue with `black` and I may fix it in the future.
        if not smart_mode:
            sublime.status_message("black: Format failed")

        return None

    return formatted


def black_format(
    source: str,
    filepath: str,
    region: sublime.Region,
    encoding: str,
    edit: sublime.Edit,
    view: sublime.View,
    smart_mode: bool,
    package_settings: SublimeSettings,
    project_settings: SublimeSettings,
):
    sublime.status_message("black: Formatting...")

    formatted = format_by_import_black_package(
        view, source, smart_mode, package_settings, project_settings
    )

    if formatted:
        write_formatted_to_source_file(
            edit, formatted, filepath, view, region, encoding
        )


def write_formatted_to_source_file(
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
