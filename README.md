<h2 align="center">python-black</h2>
<p align="center">
    <a href="https://github.com/psf/black"><img alt="black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

[Black](https://github.com/psf/black) formatter for Sublime Text.

It is recommended to use it with [LSP-pyright](https://github.com/sublimelsp/LSP-pyright).

### Installation

> There is **no need** to install `black`. However, if you choose to install it, it will not affect this package..

You can install `python-black` with Package Control:

1. Open your command pallete and type `Package Control: Install Package`.
2. Find this project `python-black` and press `Enter`.

#### ~~Local installation~~

~~This package has been uploaded to packagecontrol.io, so you do not need to choose local installation:~~

```shell
git clone https://github.com/thep0y/python-black.git
```

~~Copy or move the `python-black` folder to the `Packages` directory of **Sublime Text 4**.~~

### Usage

#### 1 Key Binding

You can create custom key binding based on sample`Preferences - Package Settings - Python Black - Key Bindings`, such as:

```json
{
  "keys": ["ctrl+super+l"],
  "command": "black",
  "args": {
    "use_selection": true
  }
}
```

The optional `use_selection` boolean (defaults to `true`) controls whether to format the selected region or the entire file.

> :warning:Note: Do not **duplicate** the key binding of other packages.

#### 2 Settings

There are some modifiable properties in settings:

```js
{
   // Whether to automatically format the entire document when saving.
   // There are three modes:
   //    - "on"
   //    - "off"
   //    - "smart": Automatic formatting is only enabled if there is a `black` section in the project's `pyproject.toml`
   "format_on_save": "on",
   // Black [OPTIONS]
   // The priority of loading options for Black is:
   // Sublime project settings > Configuration file > Sublime package user settings > Sublime package default settings
   "options": {
      // Python versions that should be supported by Black's output.
      "target_version": [],
      // How many characters per line to allow.
      "line_length": 88,
      // Format all input files like typing stubs regardless of file extension (useful when piping source on standard input).
      "is_pyi": false,
      // Skip the first line of the source code.
      "skip_source_first_line": false,
      // Don't normalize string quotes or prefixes.
      "skip_string_normalization": false,
      // Don't use trailing commas as a reason to split lines.
      "skip_magic_trailing_comma": false
   }
}

```

The `format_on_save` can also be toggled via `Preferences > Package Settings > Python Black > Format On Save`.

The Black options can also be configured in sublime-project:

```js
{
  "settings": {
    // ...
    "python-black": {
      "options": {
        "line_length": 127,
        "skip_string_normalization": true
      }
    }
  }
}
```

#### 3 Create Black Configuration File

You can quickly generate a black configuration file for the current project.

| Command                                         | Description                                                                                                                       |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `python-black: Create Black Configuration File` | Creates a `pyproject.toml` file in the root of the project with basic options. Opens the configuration file if it already exists. |

> :warning: If you don't want to generate a `pyproject.toml` for _<u>**each project**</u>_, you need to create a **global configuration file** for Black.
>
> Refer to [Black Documentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#where-black-looks-for-the-file).

> If you want to disable `format_on_save` in a project that does not use `black` code style [#14](https://github.com/thep0y/python-black/issues/14), you need to add the configuration to `*.sublime-project`:
>
> ```js
> {
> 	...
> 	"settings": {
> 		...
> 		"python-black": {
> 			"format_on_save": "off"
> 		}
> 	}
> }
> ```

### Development

If you want to fix bugs or add features, you can read the logs:

- Colorful: in `python-black.log` in the `[SublimeText]/Log` directory.

- Colorless: in the Sublime Text console.

You can also add logs where you think they should be logged as follows:

```python
from .log import child_logger

logger = child_logger(__name__)


# ...
logger.debug("...")
logger.info("...")
logger.warning("...")
logger.error("...")
# ...
```

Discussion and creation of PRs are welcome.

#### Updating vendored black library

To update the vendored version of black, replace the `python_black/lib/black` and
`python_black/lib/blib2to3` directories with the newer version.
Once replaced, the imports need to be updated to point to the vendored version.
This can be done automatically using libcst and the RewriteImportsCommand

```bash
python -m libcst.tool --no-format codemod import.RewriteImportsCommand --relative-to python_black.lib --replace black --replace blib2to3 --replace mypy_extensions --replace pathspec --replace platformdirs --replace packaging --replace tomli --replace typing_extensions --replace _black_version python_black/lib/black/
python -m libcst.tool --no-format codemod import.RewriteImportsCommand --relative-to python_black.lib --replace black --replace blib2to3 --replace mypy_extensions --replace pathspec --replace platformdirs --replace packaging --replace tomli --replace typing_extensions --replace _black_version python_black/lib/blib2to3/
```

### TODO

- [ ] format all python files in the current project
