# python-black
[Black](https://github.com/psf/black) formatter for  Sublime Text.

It is recommended to use with [LSP-pyright](https://github.com/sublimelsp/LSP-pyright).

### Installation

> There is **no need** to install `black`, but if you install it, it will not affect this package.

You can install `python-black` with package control:

1. Open your command pallete and type `Package Control: Install Package`.
2. Find this project `python-black` and press `Enter`.

#### ~~Local installation~~

~~This package has been uploaded to packagecontrol.io, so you do not need to choose local installation:~~

```shell
git clone https://github.com/thep0y/python-black.git
```

~~Copy or move the `python-black` folder to the `packages` directory of **Sublime Text 4**.~~

### Usage

#### 1 Key Binding

You can create custom key binding based on sample`Preferences - Package Settings - Python Black - Key Bindings`, such as:

```json
{
     "keys": [
         "ctrl+super+l"
     ],
     "command": "black",
     "args": {
        "use_selection": true
     }
}
```

The optional `use_selection` boolean (defaults to `true`) controls whether to format the selected region, or the entire file.

> :warning:Note: Do not **duplicate** the key binding of other packages

#### 2 Settings

There is only one modifiable property in settings:

```js
{
   // Whether to automatically format the entire document when saving.
   // There are three modes:
   //    - `true`
   //    - `false`
   //    - `"smart"`: Automatic formatting is only enabled if there is a `black` section in the project's `pyproject.toml`
   "format_on_save": true
}
```

This can also be toggled via `Preferences > Package Settings > Python Black > Format On Save`.

#### 3 Create Black Configuration File

You can quickly generate a black configuration file for the current project.

| Command                                         | Description                                                  |
| ----------------------------------------------- | ------------------------------------------------------------ |
| `python-black: Create Black Configuration File` | Creates a `pyproject.toml` file in the root of the project with basic options. Opens the configuration file if it already exists. |

> :warning: If you don't want to generate a `pyproject.toml` for *<u>**each project**</u>*, then you need to create a `black` **global configuration file**.
>
> Refer to [Black Documentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#where-black-looks-for-the-file).

>If you want to disable `format_on_save` in a project that does not use `black` code style [#14](https://github.com/thep0y/python-black/issues/14), you need to add the configuration to `*.sublime-project`:
>````json
>{
>	...
>	"settings": {
>		...
>		"python-black": {
>			"format_on_save": false
>		}
>	}
>}
>````

### Development

If you want to fix bugs or add features, you can read log:

   - Colorful: in `python-black.log` in the `[SublimeText]/Log` directory.

   - Colorless: in sublime text console.

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

### TODO

- [ ] format all python files in the current project

If someone likes or gives feedback, some features may be added in the future.

