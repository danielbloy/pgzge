The images in this directory are copied from MakeCode Arcade. I have these as in order to replicate
some of my MakeCode Arcade games using this framework. The originals can all be found
at [MakeCode Arcade](https://arcade.makecode.com/). The `player.png`
file has been renamed to `john.png` and converted using the `tools/convert_images.py`
tool to make it work properly with transparency. The command used to do this (on Windows) was:

```
PS C:\Workspace\repos\pmpge\tools> python .\convert_images.py .\john.png --out-dir converted
converted .\john.png -> converted\john.png
```
