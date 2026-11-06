# SPDX-License-Identifier: GPL-3.0-or-later
"""Properties and operators: Scan, Find Matches, Relink."""

import os

import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, FloatProperty, IntProperty,
    PointerProperty, StringProperty,
)

from . import core

# Image sources we can relink. Tiled (UDIM) images are left alone.
_RELINKABLE_SOURCES = {"FILE", "SEQUENCE"}


def missing_images():
    """Image datablocks whose file is missing.

    Skips packed, generated, UDIM and linked images (linked data is read-only).
    """
    result = []
    for image in bpy.data.images:
        if image.library is not None or image.packed_file:
            continue
        if image.source not in _RELINKABLE_SOURCES or not image.filepath:
            continue
        if not os.path.exists(bpy.path.abspath(image.filepath)):
            result.append(image)
    return result


def relink_image(image, new_path):
    """Point an image at new_path (relative if the .blend is saved) and reload it."""
    image.filepath = bpy.path.relpath(new_path) if bpy.data.filepath else new_path
    image.reload()


def results_of(context):
    """The result list of this session. It lives on the window manager, so it is never
    saved into the .blend and starts empty whenever a file is opened."""
    return context.window_manager.tr_results


def remove_results_for(results, image_names):
    """Drop the result rows for the named images, keeping the other rows as they are."""
    for index in reversed(range(len(results.items))):
        if results.items[index].image_name in image_names:
            results.items.remove(index)
    results.active_index = min(results.active_index, max(len(results.items) - 1, 0))


def _rebuild_results(results):
    """Refill the result list from the images that are missing right now."""
    results.items.clear()
    for image in missing_images():
        item = results.items.add()
        item.image_name = image.name
        item.stored_path = image.filepath
    results.active_index = 0


class TR_Item(bpy.types.PropertyGroup):
    use: BoolProperty(
        name="Relink",
        description="Relink this image when Relink is used. Untick to leave it as it is",
        default=True,
    )
    image_name: StringProperty()
    stored_path: StringProperty()
    searched: BoolProperty(default=False)
    candidate: StringProperty(description="Best file found in the search folder")
    score: FloatProperty(default=0.0)


class TR_Settings(bpy.types.PropertyGroup):
    """Choices saved with the .blend file."""

    folder: StringProperty(
        name="Folder",
        description="Folder that holds the textures. Only files directly inside it are checked",
        subtype="DIR_PATH",
    )
    threshold: FloatProperty(
        name="Threshold",
        description="Lowest match score that is accepted. 1.0 means exact names only",
        default=0.8, min=0.0, max=1.0, precision=2,
    )


class TR_Results(bpy.types.PropertyGroup):
    """Scan results for this session only (see results_of)."""

    items: CollectionProperty(type=TR_Item)
    active_index: IntProperty(default=0)


class TR_OT_scan(bpy.types.Operator):
    bl_idname = "texture_relinker.scan"
    bl_label = "Scan for Missing Textures"
    bl_description = "List image textures whose files cannot be found"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.tr_settings
        results = results_of(context)
        _rebuild_results(results)
        if not settings.folder and bpy.data.filepath:
            # Start the folder picker next to the .blend file. Store a full path:
            # Blender 5.x flags "//" as invalid in this field, and 4.2 has no option to allow it.
            settings.folder = os.path.join(os.path.dirname(bpy.data.filepath), "")
        count = len(results.items)
        self.report({"INFO"}, f"{count} missing texture(s)" if count else "No missing textures")
        return {"FINISHED"}


class TR_OT_find_matches(bpy.types.Operator):
    bl_idname = "texture_relinker.find_matches"
    bl_label = "Find Matches"
    bl_description = "Look in the search folder for a file matching each missing texture"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.tr_settings.folder) and len(results_of(context).items) > 0

    def execute(self, context):
        settings = context.scene.tr_settings
        results = results_of(context)
        folder = bpy.path.abspath(settings.folder)
        if not os.path.isdir(folder):
            self.report({"ERROR"}, f"Folder not found: {folder}")
            return {"CANCELLED"}
        candidates = core.list_image_files(folder)
        if not candidates:
            self.report({"WARNING"}, core.NO_IMAGES_IN_FOLDER)
            return {"CANCELLED"}
        candidates = core.prepare_candidates(candidates)
        found = 0
        for item in results.items:
            # threshold 0 keeps the best candidate so the slider can change later
            candidate, item.score = core.best_match_in(item.stored_path, candidates, threshold=0.0)
            item.candidate = candidate or ""
            item.searched = True
            item.use = True
            if candidate and core.passes_threshold(item.score, settings.threshold):
                found += 1
        self.report({"INFO"}, f"{found} of {len(results.items)} have a match at this threshold")
        return {"FINISHED"}


class TR_OT_relink(bpy.types.Operator):
    bl_idname = "texture_relinker.relink"
    bl_label = "Relink"
    bl_description = "Point each image at its best match, for matches at or above the threshold"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return any(item.searched and item.candidate for item in results_of(context).items)

    def execute(self, context):
        settings = context.scene.tr_settings
        results = results_of(context)
        fixed_names = set()
        for item in results.items:
            if not (item.use and item.searched and item.candidate):
                continue
            if not core.passes_threshold(item.score, settings.threshold):
                continue
            image = bpy.data.images.get(item.image_name)
            if image is None or not os.path.isfile(item.candidate):
                continue
            relink_image(image, item.candidate)
            fixed_names.add(item.image_name)
        # Drop only the fixed rows so the other rows keep their match info.
        remove_results_for(results, fixed_names)
        self.report({"INFO"}, f"Relinked {len(fixed_names)}, {len(results.items)} still missing")
        return {"FINISHED"}


# Text of the File > External Data entry.
FILE_MENU_LABEL = "Scan for Missing Textures"


def draw_file_menu(self, _context):
    self.layout.operator(TR_OT_scan.bl_idname, text=FILE_MENU_LABEL, icon="VIEWZOOM")


classes = (TR_Item, TR_Settings, TR_Results, TR_OT_scan, TR_OT_find_matches, TR_OT_relink)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tr_settings = PointerProperty(type=TR_Settings)
    bpy.types.WindowManager.tr_results = PointerProperty(type=TR_Results)
    bpy.types.TOPBAR_MT_file_external_data.append(draw_file_menu)


def unregister():
    bpy.types.TOPBAR_MT_file_external_data.remove(draw_file_menu)
    del bpy.types.WindowManager.tr_results
    del bpy.types.Scene.tr_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
