# Texture Relinker

A free Blender add-on that finds and relinks missing (pink) textures, even when the files were renamed or saved as another format.

Blender's Find Missing Files only matches exact file names. If `wood_diff.png` became `Wood_Diffuse.jpg`, it finds nothing. Texture Relinker scores every file in a folder by how close its name is, shows you each match, and relinks the ones you keep ticked. Names that differ in a number (`_08` vs `_09`, `2k` vs `4k`) are skipped on purpose.

- Get it: https://extensions.blender.org/add-ons/texture-relinker/ (or in Blender: Edit > Preferences > Get Extensions, search "Texture Relinker")
- Works with Blender 4.2 LTS and newer
- License: GPL-3.0-or-later

This repository holds the add-on's source code and is the public place to report bugs and ask questions.

## Source

The add-on is in `texture_relinker/`. It is pure Python (`bpy` and the standard library). To build an installable zip yourself:

```
blender --command extension build --source-dir texture_relinker --output-dir .
```

Then install the zip with Edit > Preferences > Get Extensions > Install from Disk.

Parts of this add-on's code were generated using an AI coding assistant and then reviewed, edited, and integrated manually.

## Report a bug

Open a new issue: https://github.com/Hher0/texture-relinker/issues/new/choose

Please include:

1. Your Blender version (Help > About Blender) and the add-on version (Edit > Preferences > Add-ons).
2. Your operating system.
3. The steps you took, and what you expected to happen.
4. A screenshot of the Relink tab in the 3D Viewport sidebar after Find Matches.
5. If a file was matched wrong or not matched: the old file name stored in the .blend and the name of the file on disk.

Please don't attach .blend files or textures you are not allowed to share. File names are usually enough.
