import bpy

import re

from typing import Union

last_operations = ""


def filter_none_bpy_lines(text: str):
    filtered = []
    for line in text.split("\n"):
        if re.search(r"^bpy\.", line) is None:
            continue
        filtered.append(line)
    return "\n".join(filtered)


def get_recent_operations() -> str:
    global last_operations
    window = bpy.context.window_manager.windows[0]

    override_context = bpy.context.copy()
    override_context["window"] = window
    override_context["screen"] = window.screen
    override_context["area"] = window.screen.areas[0]
    old_type = override_context["area"].type
    override_context["area"].type = "INFO"

    bpy.ops.info.select_all(override_context, action="SELECT")
    bpy.ops.info.report_copy(override_context)

    clipboard = bpy.context.window_manager.clipboard

    override_context["area"].type = old_type

    removefor = str(last_operations)
    last_operations = str(clipboard)

    result = str(clipboard).replace(removefor, "")

    return filter_none_bpy_lines(result)


def flush_recent_operations():
    get_recent_operations()
