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
     "command": "black"
}
```

> :warning:Note: Do not **duplicate** the key binding of other packages

#### 2 Settings

There is only one modifiable property in settings:

```js
{
   // Whether to automatically format the entire document when saving
   "format_on_save": true
}
```

#### 3 Create Black Configuration File

You can quickly generate a black configuration file for the current project.

| Command                                         | Description                                                  |
| ----------------------------------------------- | ------------------------------------------------------------ |
| `python-black: Create Black Configuration File` | Creates a `pyproject.toml` file in the root of the project with basic options. Opens the configuration file if it already exists. |

### TODO

- [ ] format all python files in the current project

If someone likes or gives feedback, some features may be added in the future.

