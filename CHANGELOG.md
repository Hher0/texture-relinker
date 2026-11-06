# Changelog

## 0.1.2
- Scan results and match lists now belong to the current session (stored on the window manager) instead of the scene. They are never saved into the .blend and start empty when a file is opened, so the add-on no longer needs a file-load handler.
- Folder and Threshold are still saved with the .blend.
- After Undo, click Scan again to list images that are missing again.

## 0.1.1
- After Scan, the Folder field starts at the folder of the saved .blend as a full path. It used to be "//", which Blender 5.x marks as invalid and shows in red. Matching worked either way.

## 0.1.0
- Scan lists image textures whose files are missing (packed, generated, UDIM and linked images are skipped).
- Find Matches looks in one folder and scores each file: exact name, same name with another extension, then fuzzy name.
- Names that differ in a number (`_08` and `_09`, `2k` and `4k`) are treated as different files.
- Each match has a tick box, so a row can be left out before Relink.
- Relink applies ticked matches at or above the threshold slider (default 0.8), uses relative paths when the .blend is saved, and reports how many were fixed.
- Rows with no good match say so, and show the best score and file name (on separate lines so neither is cut off in a narrow sidebar).
- Result rows give the texture name most of the width: the score sits in a narrow column on the right.
- Find Matches stops with a warning when the folder has no images, so the warning stays visible.
- Matching stays fast on big folders: about 1 second for 50 missing textures against 3000 files.
- The folder picker opens next to the saved .blend file.
- Results and folders from another computer are cleared when a file is opened.
- N panel tab "Relink" and a File > External Data entry.
