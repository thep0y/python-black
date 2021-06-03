# python-black
[Black](https://github.com/psf/black) formatter for  Sublime Text

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

