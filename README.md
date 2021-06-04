# python-black
[Black](https://github.com/psf/black) formatter for  Sublime Text.

It is recommended to use with [LSP-pyright](https://github.com/sublimelsp/LSP-pyright).

![output](https://cdn.jsdelivr.net/gh/thep0y/image-bed/md/1622806610596.png)

### Installation

If you haven't install `black`, just install it:

```shell
pip install black
```

~~You can install `python-black` with package control:~~

1. ~~Open your command pallete and type `Package Control: Install Package`.~~
2. ~~Find this project `python-black` and press `Enter`.~~

#### Local installation

This package has not been uploaded to packagecontrol.io, so it needs to be installed locally:

```shell
git clone https://github.com/thep0y/python-black.git
```

Copy or move the `python-black` folder to the `packages` directory of **Sublime Text 4**.

### Usage

#### 1 key binding

In order to prevent conflicts with the key binding of other packages, no default key binding is provided.
You can customize `python-black` key binding, and command is `black`.

Example:

```json
{
     "keys": [
         "ctrl+super+l"
     ],
     "command": "black"
}
```

> :warning:Note: Do not **duplicate** the key binding of other packages

#### 2 Create Black Configuration File

You can quickly generate a black configuration file for the current project.

| Command                                         | Description                                                  |
| ----------------------------------------------- | ------------------------------------------------------------ |
| `python-black: Create Black Configuration File` | Creates a `pyproject.toml` file in the root of the project with basic options. Opens the configuration file if it already exists. |

### Settings

```js
{
   // If the `black` command is not in the current environment variable, 
   // you need to fill in its absolute path
   "command": "black"
}
```

### TODO

If someone likes or gives feedback, some features may be added in the future.

