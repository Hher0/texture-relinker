# SPDX-License-Identifier: GPL-3.0-or-later
"""Texture Relinker: find and relink missing textures with fuzzy name matching."""

from . import operators, ui


def register():
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
