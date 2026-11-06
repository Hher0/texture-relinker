# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar panel (3D Viewport > N panel > Relink tab)."""

import bpy

from . import core, operators

# When False the panel hides the single Folder, Find Matches and Relink controls,
# for builds that register their own search section under this panel.
show_folder_controls = True

# Width of the percent column in a result row, in UI units. The name gets the rest.
_PERCENT_WIDTH = 2.0


class TR_UL_missing(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        settings = context.scene.tr_settings
        status = core.match_status(item.searched, item.candidate, item.score, settings.threshold)
        row = layout.row(align=True)
        if status == "match":
            # The tick box already marks a match, so no icon: the name gets the space.
            row.prop(item, "use", text="")
            row.label(text=item.image_name)
            percent = row.row(align=True)
            percent.alignment = "RIGHT"
            percent.ui_units_x = _PERCENT_WIDTH
            percent.label(text=f"{item.score:.0%}")
        else:
            icon_name = {"missing": "ERROR", "no_match": "CANCEL", "below": "QUESTION"}[status]
            row.label(text=item.image_name, icon=icon_name)


class TR_PT_panel(bpy.types.Panel):
    bl_label = "Texture Relinker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Relink"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.tr_settings
        results = operators.results_of(context)

        layout.operator(operators.TR_OT_scan.bl_idname, icon="VIEWZOOM")
        if not results.items:
            return

        layout.template_list("TR_UL_missing", "", results, "items", results, "active_index", rows=4)
        if 0 <= results.active_index < len(results.items):
            item = results.items[results.active_index]
            status = core.match_status(item.searched, item.candidate, item.score, settings.threshold)
            box = layout.box()
            box.label(text=core.filename_of(item.stored_path), icon="IMAGE_DATA")
            folder = core.folder_of(item.stored_path)
            if folder:
                box.label(text=folder)
            if status != "missing":
                box.label(text=core.match_summary(status, item.score))
                if item.candidate:
                    box.label(text=core.filename_of(item.candidate))

        layout.separator()
        if show_folder_controls:
            layout.prop(settings, "folder")
        layout.prop(settings, "threshold", slider=True)
        if show_folder_controls:
            layout.operator(operators.TR_OT_find_matches.bl_idname, icon="FILE_FOLDER")
            layout.operator(operators.TR_OT_relink.bl_idname, icon="FILE_REFRESH")


classes = (TR_UL_missing, TR_PT_panel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
