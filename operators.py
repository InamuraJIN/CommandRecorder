import bpy
from bpy.props import StringProperty, IntProperty

from .utils.report import flush_recent_operations, get_recent_operations
from .utils.macro import (
    add_to_local_macro,
    create_local_macro,
    get_local_macro,
    list_local_macro_names,
    move_to_global,
    move_to_local,
    read_from_global_macro,
    read_from_local_macro,
    remove_global_macro,
    remove_local_macro, rename_global_macro,
    rename_local_macro,
)
from .state import (
    clear_global_active,
    clear_local_active,
    set_global_active,
    set_local_active,
    state,
)


class TestOpOperator(bpy.types.Operator):
    bl_idname = "command_recorder.testop"
    bl_label = "TestOp"

    def execute(self, context):
        recent = get_recent_operations()
        print("####################")
        print("recent:" + str(recent))
        print("####################")

        return {"FINISHED"}


def record_command():
    commands = get_recent_operations()

    if state["local_macro_active_name"] is None:
        raise ValueError("No macro is selected.")

    print('state["local_macro_active_name"]:' + str(state["local_macro_active_name"]))
    add_to_local_macro(state["local_macro_active_name"], commands)


def play_command(category: str, name: str):
    commands = None

    print("category:" + str(category))
    print("name:" + str(name))

    if category == "global":
        commands = read_from_global_macro(name)

    if category == "local":
        commands = read_from_local_macro(name)

    print("commands:" + str(commands))
    if commands is not None:
        exec(commands)
        return

    raise ValueError("No commands!")


class RecordCommandOperator(bpy.types.Operator):
    bl_idname = "command_recorder.recordcommand"
    bl_label = "RecordCommand"

    state_running = False

    def cls(self):
        return RecordCommandOperator

    @classmethod
    def poll(cls, self):
        return state["local_macro_active_name"] != ""

    def __start(self, context):
        self.cls().state_running = True
        flush_recent_operations()
        self.report({"INFO"}, "Record Start")

    def __end(self, context):
        self.cls().state_running = False
        record_command()
        self.report({"INFO"}, "Record End")

    def invoke(self, context, event):
        if not self.cls().state_running:
            self.__start(context)
            return {"FINISHED"}
        else:
            self.__end(context)
        return {"FINISHED"}

    def execute(self, context):
        return {"FINISHED"}


class PlayCommandOperator(bpy.types.Operator):
    bl_idname = "command_recorder.playcommand"
    bl_label = "PlayCommand"

    type = StringProperty(
        name="MacroCategory", description="local or global", default="Local",
    )

    name = StringProperty(name="MacroName", description="name of a macro", default="",)

    @classmethod
    def poll(cls, self):
        return not RecordCommandOperator.state_running

    def execute(self, context):
        self.report({"INFO"}, str((self.type)))
        self.report({"INFO"}, str((self.name)))
        play_command(self.type, self.name)
        return {"FINISHED"}


class SelectGlobalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.selectglobalmacro"
    bl_label = "SelectGlobalMacro"

    name = StringProperty(name="Macro Name", description="name of macro", default="",)

    @classmethod
    def poll(cls, self):
        return not RecordCommandOperator.state_running

    def execute(self, context):
        set_global_active(self.name)
        return {"FINISHED"}


class RemoveGlobalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.removeglobalmacro"
    bl_label = "RemoveGlobalMacro"

    @classmethod
    def poll(cls, context):
        return state["global_macro_active_name"] != ""

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        name = state["global_macro_active_name"]
        remove_global_macro(name)
        return {"FINISHED"}


class RenameGlobalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.renameglobalmacro"
    bl_label = "RenameGlobalMacro"


    name = StringProperty(
        name="New Name", description="new name of the macro", default="",
    )

    @classmethod
    def poll(cls, context):
        return state["global_macro_active_name"] != ""

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        if self.name == "":
            self.report({"ERROR"}, str(("Empty string is not allowed.")))
            return {"CANCELLED"}

        if read_from_global_macro(self.name) is not None:
            self.report({"ERROR"}, str(("Already exists.")))
            return {"CANCELLED"}

        rename_global_macro(state["global_macro_active_name"], self.name)
        set_global_active(self.name)

        return {"FINISHED"}


class MoveMacroToLocalOperator(bpy.types.Operator):
    bl_idname = "command_recorder.movemacrotolocal"
    bl_label = "MoveMacroToLocal"

    @classmethod
    def poll(cls, context):
        return (
            state["global_macro_active_name"] != ""
            and read_from_local_macro(state["global_macro_active_name"]) is None
        )

    def execute(self, context):
        name = state["global_macro_active_name"]
        move_to_local(name)
        clear_global_active()
        clear_local_active()
        set_local_active(name)
        return {"FINISHED"}


class SelectLocalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.selectlocalmacro"
    bl_label = "SelectLocalMacro"

    name = StringProperty(name="Macro Name", description="name of macro", default="",)

    @classmethod
    def poll(cls, self):
        return not RecordCommandOperator.state_running

    def execute(self, context):
        set_local_active(self.name)
        return {"FINISHED"}


class AddLocalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.addlocalmacro"
    bl_label = "AddLocalMacro"

    @classmethod
    def poll(cls, self):
        return not RecordCommandOperator.state_running

    def execute(self, context):
        create_local_macro("NEW MACRO")
        return {"FINISHED"}


class RemoveLocalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.remove_local_macro"
    bl_label = "remove_local_macro"

    @classmethod
    def poll(cls, context):
        return state["local_macro_active_name"] != ""

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        remove_local_macro(state["local_macro_active_name"])
        clear_local_active()
        return {"FINISHED"}


class RenameLocalMacroOperator(bpy.types.Operator):
    bl_idname = "command_recorder.renamelocalmacro"
    bl_label = "RenameLocalMacro"

    name = StringProperty(
        name="New Name", description="new name of the macro", default="",
    )

    @classmethod
    def poll(cls, context):
        return state["local_macro_active_name"] != ""

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        if self.name == "":
            self.report({"ERROR"}, str(("Empty string is not allowed.")))
            return {"CANCELLED"}

        if read_from_local_macro(self.name) is not None:
            self.report({"ERROR"}, str(("Already exists.")))
            return {"CANCELLED"}

        rename_local_macro(state["local_macro_active_name"], self.name)
        set_local_active(self.name)

        return {"FINISHED"}


class MoveMacroToGlobalOperator(bpy.types.Operator):
    bl_idname = "command_recorder.movemacrotoglobal"
    bl_label = "MoveMacroToGlobal"

    @classmethod
    def poll(cls, context):
        return (
            state["local_macro_active_name"] != ""
            and read_from_global_macro(state["local_macro_active_name"]) is None
        )

    def execute(self, context):
        name = state["local_macro_active_name"]
        move_to_global(name)
        clear_global_active()
        clear_local_active()
        set_global_active(name)
        return {"FINISHED"}
