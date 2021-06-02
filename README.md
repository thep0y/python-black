# python-black
[Black](https://github.com/psf/black) formatter for  Sublime Text

### Installation

If you haven't install `black`, just install it:

```shell
pip install black
```

You can install `python-black` with package control:

1. Open your command pallete and type `Package Control: Install Package`.
2. Find this project `python-black` and press `Enter`.

### Usage

Press <kbd>Ctrl</kbd>+<kbd>Super</kbd>+<kbd>L</kbd> to format current file.

### Settings

```
{
   // If the `black` command is not in the current environment variable, 
   // you need to fill in its absolute path
   "command": "black",

   // Maximum length of each line
   "max-line-length": 88,

   // The python version used by the file to be formatted.
   // If you fill in more than one, only the first one will take effect.
   // Available Options:
   //     [py27 py33 py34 py35 py36 py37 py38 py39]
   "target-version": []
}
```

### TODO

If someone likes or gives feedback, some features may be added in the future.

