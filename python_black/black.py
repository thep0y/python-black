import sublime
import os
import sys

from pathlib import Path
from typing import Optional, Any, Dict, Tuple, List

from black import format_str  # type: ignore
from black.mode import Mode, TargetVersion  # type: ignore
from black.files import find_pyproject_toml, parse_pyproject_toml  # type: ignore
from black.const import DEFAULT_LINE_LENGTH, DEFAULT_INCLUDES  # type: ignore


def out(msg: str):
    return sublime.status_message(msg)


def target_version_option_callback(v: Tuple[str, ...]) -> List[TargetVersion]:
    return [TargetVersion[val.upper()] for val in v]


def find_global_config_file() -> Optional[str]:
    HOME = str(Path.home())

    if sys.platform == "win32":
        config_file = os.path.join(HOME, ".black")
    else:
        config_file = os.path.join(HOME, ".config", "black")

    if os.path.exists(config_file) and os.path.isfile(config_file):
        return config_file
    return None


def read_pyproject_toml(
    config_file: Optional[str], default_config: Optional[Dict[str, Any]], src: Tuple[str, ...]
) -> Tuple[Optional[dict], Optional[str]]:
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
    if not config_file:
        config_file = find_pyproject_toml(src)
        if not config_file:
            # find global config file
            config_file = find_global_config_file()
            if not config_file:
                return default_config, None

    try:
        config = parse_pyproject_toml(config_file)
    except (OSError, ValueError, FileNotFoundError) as e:
        raise Exception(f"Error reading configuration file: {e}")

    if not config:
        return default_config, None
    else:
        config = {k: str(v) if not isinstance(v, (list, dict)) else v for k, v in config.items()}

    target_version = config.get("target_version")
    if target_version is not None and not isinstance(target_version, list):
        raise AttributeError("target-version: Config key target-version must be a list")

    default_map: Dict[str, Any] = {}
    if default_config:
        default_map.update(default_config)

    default_map.update(config)

    return default_map, config_file


def really_format(code: str, src: Tuple[str, ...], config_file: Optional[str] = None) -> Optional[str]:
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
    default_config = {
        "line_length": DEFAULT_LINE_LENGTH,
        "skip_string_normalization": True,
        "skip_magic_trailing_comma": True,
        "experimental_string_processing": True,
        "include": DEFAULT_INCLUDES,
    }

    default_config, config_file = read_pyproject_toml(config_file, default_config, src)
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
        line_length=int(default_config['line_length']),
        is_pyi=False,
        string_normalization=not default_config['skip_string_normalization'],
        magic_trailing_comma=not default_config['skip_magic_trailing_comma'],
        experimental_string_processing=default_config['experimental_string_processing'],
    )

    if code is not None:
        formatted = format_str(code, mode=mode)
        return formatted
