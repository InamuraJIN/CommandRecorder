import inspect
from typing import Callable, List

def get_bpy_classes(module, reverse=False):
    module_items = inspect.getmembers(module)
    bpy_classes = []
    for module_item in module_items:
        name, item = module_item
        if hasattr(item, "bl_idname"):
            bpy_classes.append(item)

    if reverse:
        bpy_classes.reverse()

    return bpy_classes

def forEach(items:List, func:Callable):
    for item in items:
        try:
            func(item)
        except Exception as error:
            print('error:' + str(error))
            
        
