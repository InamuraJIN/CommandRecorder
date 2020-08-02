from typing import Union


state = {
    "global_macro_active_name": "",
    "local_macro_active_name":"",
    "global_macro_names": None,
}

def set_global_active(name:str):
    state["global_macro_active_name"] = name

def set_local_active(name:str):
    state["local_macro_active_name"] = name

def clear_global_active():
    state["global_macro_active_name"] = ""

def clear_local_active():
    state["local_macro_active_name"] = ""



