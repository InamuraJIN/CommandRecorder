# ==============================================================
# スタートアップ
# -------------------------------------------------------------------------------------------
import bpy  # Blender内部のデータ構造にアクセスするために必要
from bpy.app.handlers import persistent
import os
import shutil
import json
from json.decoder import JSONDecodeError
from typing import List

from bpy.props import (  # プロパティを使用するために必要
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Panel, UIList, Operator, PropertyGroup


from . import DefineCommon as Common


# ==============================================================
# 使用クラスの宣言
# -------------------------------------------------------------------------------------------
class CR_OT_String(PropertyGroup):  # リストデータを保持するためのプロパティグループを作成
    Command: StringProperty(default="")  # CR_Var.name


class CR_List_Selector(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.name)


class CR_List_Command(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.name)


class CR_List_Instance(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.name)


# -------------------------------------------------------------------------------------------


def CR_(Data, Num):
    scene = bpy.context.scene
    if Data == "List":
        return eval("scene.CR_Var.List_Command_{0:03d}".format(Num))
    elif Data == "Index":
        return eval("scene.CR_Var.List_Index_{0:03d}".format(Num))
    else:
        exec("scene.CR_Var.List_Index_{0:03d} = {1}".format(Num, Data))


def get_recent_operations(get_type: str = "") -> List[str]:  # 操作履歴にアクセス
    # remove other Recent Reports
    reports = [
        bpy.data.texts.remove(t, do_unlink=True)
        for t in bpy.data.texts
        if t.name.startswith("Recent Reports")
    ]
    # make a report
    win = bpy.context.window_manager.windows[0]
    area = win.screen.areas[0]
    area_type = area.type
    area.type = "INFO"
    override = bpy.context.copy()
    override["window"] = win
    override["screen"] = win.screen
    override["area"] = win.screen.areas[0]
    bpy.ops.info.select_all(override, action="SELECT")
    bpy.ops.info.report_copy(override)
    area.type = area_type
    clipboard = bpy.context.window_manager.clipboard
    bpy.data.texts.new("Recent Reports")
    bpy.data.texts["Recent Reports"].write(clipboard)
    # print the report
    return bpy.data.texts["Recent Reports"].lines  # 操作履歴全ての行


def record(index, mode):
    recent_operations = get_recent_operations()
    if mode == "Start":
        CR_PT_List.Bool_Record = 1
        CR_Prop.Temp_Num = len(recent_operations)
    else:
        CR_PT_List.Bool_Record = 0
        for i in range(CR_Prop.Temp_Num, len(recent_operations)):
            TempText = recent_operations[i - 1].body
            if TempText.count("bpy"):
                Item = CR_("List", index).add()
                Item.name = TempText[TempText.find("bpy") :]


temp_json_path = os.path.dirname(__file__) + "/temp.json"
first_open = [True]
temp_count = [0]


def temp_save(index):  # write new command to temp.json file
    if os.path.exists(temp_json_path):
        if first_open[0]:
            first_open[0] = False
            with open(temp_json_path, "r+", encoding="utf8") as tempfile:
                tempfile.truncate(0)
                tempfile.seek(0)
                json.dump({"0": []}, tempfile)
    else:
        with open(temp_json_path, "w", encoding="utf8") as tempfile:
            json.dump({"0": []}, tempfile)
    with open(temp_json_path, "r+", encoding="utf8") as tempfile:
        data = json.load(tempfile)
        data.update({str(index): []})
        data["0"].append(CR_("List", 0)[index - 1]["name"])
        tempfile.seek(0)
        json.dump(data, tempfile)


def temp_update():  # update all commands in temp.json file
    with open(temp_json_path, "r+", encoding="utf8") as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        data = {}
        for cmd in range(len(CR_("List", 0)) + 1):
            data.update({str(cmd): [i.name for i in CR_("List", cmd)]})
        json.dump(data, tempfile)


def temp_update_command(index):  # update one command in temp.json file
    print(temp_json_path)
    with open(temp_json_path, "r+", encoding="utf8") as tempfile:
        data = json.load(tempfile)
        data[str(index)] = [i.name for i in CR_("List", int(index))]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)


@persistent
def temp_load(dummy):  # load commands after undo
    if bpy.context.scene.CR_Var.IgnoreUndo:
        with open(temp_json_path, "r", encoding="utf8") as tempfile:
            data = json.load(tempfile)
        command = CR_("List", 0)
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.name = data["0"][i - 1]
            record = CR_("List", i)
            record.clear()
            for j in range(len(data[keys[i]])):
                Item = record.add()
                Item.name = data[keys[i]][j]


bpy.app.handlers.undo_post.append(
    temp_load
)  # add TempLoad to ActionHandler and call ist after undo


def add(index):
    recent_operations = get_recent_operations("Reports_All")
    if index or len(CR_("List", 0)) < 250:
        item = CR_("List", index).add()
        if index:
            if recent_operations[-2].body.count("bpy"):
                Name_Temp = recent_operations[-2].body
                item.name = Name_Temp[Name_Temp.find("bpy") :]
            else:
                Name_Temp = recent_operations[-3].body
                item.name = Name_Temp[Name_Temp.find("bpy") :]
        else:
            item.name = "Untitled_{0:03d}".format(len(CR_("List", index)))
        CR_(len(CR_("List", index)) - 1, index)


def remove(index):
    if not index:
        for Num_Loop in range(CR_("Index", 0) + 1, len(CR_("List", 0)) + 1):
            CR_("List", Num_Loop).clear()
            for Num_Command in range(len(CR_("List", Num_Loop + 1))):
                Item = CR_("List", Num_Loop).add()
                Item.name = CR_("List", Num_Loop + 1)[Num_Command].name
            CR_(CR_("Index", Num_Loop + 1), Num_Loop)
    if len(CR_("List", index)):
        CR_("List", index).remove(CR_("Index", index))
        if len(CR_("List", index)) - 1 < CR_("Index", index):
            CR_(len(CR_("List", index)) - 1, index)
            if CR_("Index", index) < 0:
                CR_(0, index)


def move(index, mode):
    index1 = CR_("Index", index)
    if mode == "Up":
        index2 = CR_("Index", index) - 1
    else:
        index2 = CR_("Index", index) + 1
    LengthTemp = len(CR_("List", index))
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
        CR_("List", index).move(index1, index2)
        CR_(index2, index)

        # コマンドの入れ替え処理
        if not index:
            index1 += 1
            index2 += 1
            CR_("List", 254).clear()
            # 254にIndex2を逃がす
            for Num_Command in CR_("List", index2):
                Item = CR_("List", 254).add()
                Item.name = Num_Command.name
            CR_(CR_("Index", index2), 254)
            CR_("List", index2).clear()
            # Index1からIndex2へ
            for Num_Command in CR_("List", index1):
                Item = CR_("List", index2).add()
                Item.name = Num_Command.name
            CR_(CR_("Index", index1), index2)
            CR_("List", index1).clear()
            # 254からIndex1へ
            for Num_Command in CR_("List", 254):
                Item = CR_("List", index1).add()
                Item.name = Num_Command.name
            CR_(CR_("Index", 254), index1)
            CR_("List", 254).clear()


def select_command(mode: str):
    current_index = CR_("Index", 0)
    list_length = len(CR_("List", 0)) - 1
    if mode == "Up":
        if current_index == 0:
            bpy.context.scene.CR_Var.List_Index_000 = list_length
        else:
            bpy.context.scene.CR_Var.List_Index_000 = current_index - 1
    else:
        if current_index == list_length:
            bpy.context.scene.CR_Var.List_Index_000 = 0
        else:
            bpy.context.scene.CR_Var.List_Index_000 = current_index + 1


def play(Commands):
    scene = bpy.context.scene
    if scene.CR_Var.Target_Switch == "Once":  # Target Switch is always 'Once'
        for Command in Commands:
            if type(Command) == str:
                exec(Command)
            else:
                exec(Command.name)
    else:
        current_mode = bpy.context.mode
        Set_DeSelect = ""
        Set_Select = []
        Set_Active = []
        if current_mode == "OBJECT":
            Set_DeSelect = "bpy.ops.object.select_all(action='DESELECT')"
            for Target in bpy.context.selected_objects:
                Set_Select.append(
                    "bpy.data.objects['{0}'].select = True".format(Target.name)
                )
                Set_Active.append(
                    "bpy.context.scene.objects.active = bpy.data.objects['{0}']".format(
                        Target.name
                    )
                )
        elif current_mode == "EDIT_MESH":
            pass

        elif current_mode == "EDIT_ARMATURE":
            Arm = bpy.context.scene.objects.active.name
            Set_DeSelect = "bpy.ops.armature.select_all(action='DESELECT')"
            for Target in bpy.context.selected_editable_bones:
                Set_Select.append(
                    "bpy.data.objects['{0}'].data.edit_bones['{1}'].select = True".format(
                        Arm, Target.name
                    )
                )
                Set_Active.append(
                    "bpy.data.objects['{0}'].data.edit_bones.active = bpy.data.objects['{0}'].data.edit_bones['{1}']".format(
                        Arm, Target.name
                    )
                )

        elif current_mode == "POSE":
            Arm = bpy.context.scene.objects.active.name
            Set_DeSelect = "bpy.ops.pose.select_all(action='DESELECT')"
            for Target in bpy.context.selected_pose_bones:
                print("a")
                Set_Select.append(
                    "bpy.data.objects['{0}'].pose.bones['{1}'].bone.select = True".format(
                        Arm, Target.name
                    )
                )
                Set_Active.append(
                    "bpy.data.objects['{0}'].data.bones.active = bpy.data.objects['{0}'].data.bones['{1}']".format(
                        Arm, Target.name
                    )
                )

        for Num_Loop in range(len(Set_Select)):
            print(Set_DeSelect)
            print(Set_Select[Num_Loop])
            print(Set_Active[Num_Loop])
            exec(Set_DeSelect)
            exec(Set_Select[Num_Loop])
            exec(Set_Active[Num_Loop])
            if current_mode == "EDIT_ARMATURE":
                bpy.ops.object.mode_set(mode="POSE")
                bpy.ops.object.mode_set(mode="EDIT")
            for Command in Commands:
                if type(Command) == str:
                    exec(Command)
                else:
                    exec(Command.name)


def clear(index):
    CR_("List", index).clear()


class CR_OT_Selector(Operator):
    bl_idname = "cr_selector.button"  # 大文字禁止
    bl_label = "Button_Selector"  # メニューに登録される名前
    # bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    mode: bpy.props.StringProperty(default="")

    def execute(self, context):
        scene = bpy.context.scene
        # 追加
        if self.mode == "Add":
            add(0)
            if scene.CR_Var.IgnoreUndo:
                temp_save(CR_("Index", 0) + 1)
        # 削除
        elif self.mode == "Remove":
            remove(0)
            if scene.CR_Var.IgnoreUndo:
                temp_update()
        # 上へ
        elif self.mode == "Up":
            move(0, "Up")
            if scene.CR_Var.IgnoreUndo:
                temp_update()
        # 下へ
        elif self.mode == "Down":
            move(0, "Down")
            if scene.CR_Var.IgnoreUndo:
                temp_update()
        bpy.context.area.tag_redraw()
        return {"FINISHED"}  # UI系の関数の最後には必ず付ける


class CR_OT_Selector_Up(Operator):
    bl_idname = "cr_selector_up.button"
    bl_label = "Command_OT_Selection_Up"
    # bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        select_command("Up")
        bpy.context.area.tag_redraw()
        return {"FINISHED"}


class CR_OT_Selector_Down(Operator):
    bl_idname = "cr_selector_down.button"
    bl_label = "Command_OT_Selection_Down"
    # bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        select_command("Down")
        bpy.context.area.tag_redraw()
        return {"FINISHED"}


class Command_OT_Play(Operator):
    bl_idname = "cr_commandplay.button"  # 大文字禁止
    bl_label = "Command_OT_Play"  # メニューに登録される名前
    bl_options = {"REGISTER", "UNDO"}  # アンドゥ履歴に登録

    def execute(self, context):
        # コマンドを実行
        play(CR_("List", CR_("Index", 0) + 1))
        return {"FINISHED"}  # UI系の関数の最後には必ず付ける


class Command_OT_Add(Operator):
    bl_idname = "cr_commandadd.button"  # 大文字禁止
    bl_label = "Command_OT_Add"  # メニューに登録される名前
    # bl_options = {'REGISTER', 'UNDO'}#アンドゥ履歴に登録
    def execute(self, context):
        # コマンドを実行
        add(CR_("Index", 0) + 1)
        if bpy.context.scene.CR_Var.IgnoreUndo:
            temp_update_command(CR_("Index", 0) + 1)
        bpy.context.area.tag_redraw()
        return {"FINISHED"}  # UI系の関数の最後には必ず付ける


class CR_OT_Command(Operator):
    bl_idname = "cr_command.button"  # 大文字禁止
    bl_label = "Button_Command"  # メニューに登録される名前
    # bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    mode: bpy.props.StringProperty(default="")

    def execute(self, context):
        scene = bpy.context.scene
        # 録画を開始
        if self.mode == "Record_Start":
            record(CR_("Index", 0) + 1, "Start")
        # 録画を終了
        elif self.mode == "Record_Stop":
            record(CR_("Index", 0) + 1, "Stop")
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)
        # 追加
        elif self.mode == "Add":
            add(CR_("Index", 0) + 1)
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)
        # 削除
        elif self.mode == "Remove":
            remove(CR_("Index", 0) + 1)
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)
        # 上へ
        elif self.mode == "Up":
            move(CR_("Index", 0) + 1, "Up")
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)
        # 下へ
        elif self.mode == "Down":
            move(CR_("Index", 0) + 1, "Down")
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)
        # リストをクリア
        elif self.mode == "Clear":
            clear(CR_("Index", 0) + 1)
            if scene.CR_Var.IgnoreUndo:
                temp_update_command(CR_("Index", 0) + 1)

        bpy.context.area.tag_redraw()
        return {"FINISHED"}  # UI系の関数の最後には必ず付ける


def strage_file():
    folder_name = "Storage"
    file_name = "CommandRecorder_Storage.txt"
    preset_data_name = "CommandRecorder_Storage_Preset.txt"
    addon_directory = os.path.dirname(os.path.abspath(__file__))
    filepath = addon_directory
    filepath = os.path.join(filepath, folder_name)
    filepath = os.path.join(filepath, file_name)
    destination_path = os.path.normpath(filepath)
    if os.path.exists(destination_path):
        return destination_path
    else:
        source_path = os.path.join(addon_directory, preset_data_name)
        shutil.copyfile(source_path, destination_path)
        if os.path.exists(destination_path):
            return destination_path
    raise ValueError("Destination Not Exists.")


def save():
    scene = bpy.context.scene
    with open(strage_file(), "w") as file:
        names = scene.CR_Var.Instance_Name
        commands = scene.CR_Var.Instance_Command
        for index in range(len(names)):
            file.write("CR_Name" + "\n" + names[index] + "\n")
            file.write("CR_Command" + "\n")
            for command in commands[index]:
                file.write(command + "\n")
            file.write("CR_End" + "\n\n")


def load():
    scene = bpy.context.scene
    with open(strage_file(), "r") as file:
        lines = []
        for line in file:
            lines.append(line.replace("\n", ""))
        file.close()  # ファイルを閉じる

    append_command_flag = 0 # ???
    temp_commands = []
    count = 0
    scene.CR_Var.Instance_Name.clear()
    scene.CR_Var.Instance_Command.clear()
    for index in range(len(lines)):
        if lines[index] == "CR_Name":
            scene.CR_Var.Instance_Name.append(lines[index + 1])
        elif lines[index] == "CR_Command":
            append_command_flag = 1
        elif lines[index] == "CR_End":
            append_command_flag = 0
            scene.CR_Var.Instance_Command.append(temp_commands)
            temp_commands = []
            count += 1
        if append_command_flag > 0:
            if append_command_flag > 1:
                temp_commands.append(lines[index])
            append_command_flag += 1


def recorder_to_instance():
    CR_Prop.Instance_Name.append(CR_("List", 0)[CR_("Index", 0)].name)
    Temp_Command = []
    for Command in CR_("List", CR_("Index", 0) + 1):
        Temp_Command.append(Command.name)
    CR_Prop.Instance_Command.append(Temp_Command)


def instance_to_recorder():
    scene = bpy.context.scene
    Item = CR_("List", 0).add()
    Item.name = CR_Prop.Instance_Name[int(scene.CR_Var.Instance_Index)]
    for Command in CR_Prop.Instance_Command[int(scene.CR_Var.Instance_Index)]:
        Item = CR_("List", len(CR_("List", 0))).add()
        Item.name = Command
    CR_(len(CR_("List", 0)) - 1, 0)


def execute_instance(index):
    play(CR_Prop.Instance_Command[index])


def rename_instance():
    scene = bpy.context.scene
    CR_Prop.Instance_Name[int(scene.CR_Var.Instance_Index)] = scene.CR_Var.Rename


def i_remove():
    scene = bpy.context.scene
    if len(CR_Prop.Instance_Name):
        Index = int(scene.CR_Var.Instance_Index)
        CR_Prop.Instance_Name.pop(Index)
        CR_Prop.Instance_Command.pop(Index)
        if len(CR_Prop.Instance_Name) and len(CR_Prop.Instance_Name) - 1 < Index:
            scene.CR_Var.Instance_Index = str(len(CR_Prop.Instance_Name) - 1)


def i_move(mode):
    scene = bpy.context.scene
    index1 = int(scene.CR_Var.Instance_Index)
    if mode == "Up":
        index2 = int(scene.CR_Var.Instance_Index) - 1
    else:
        index2 = int(scene.CR_Var.Instance_Index) + 1
    LengthTemp = len(CR_Prop.Instance_Name)
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 < LengthTemp):
        CR_Prop.Instance_Name[index1], CR_Prop.Instance_Name[index2] = (
            CR_Prop.Instance_Name[index2],
            CR_Prop.Instance_Name[index1],
        )
        CR_Prop.Instance_Command[index1], CR_Prop.Instance_Command[index2] = (
            CR_Prop.Instance_Command[index2],
            CR_Prop.Instance_Command[index1],
        )
        scene.CR_Var.Instance_Index = str(index2)


class CR_OT_Instance(Operator):
    bl_idname = "cr_instance.button"  # 大文字禁止
    bl_label = "Button_Instance"  # メニューに登録される名前
    # bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    mode: bpy.props.StringProperty(default="")

    def execute(self, context):
        # 追加
        if self.mode == "Add":
            add(255)
        # 削除
        elif self.mode == "Remove":
            remove(255)
        # 上へ
        elif self.mode == "Up":
            Up(255)
        # 下へ
        elif self.mode == "Down":
            Down(255)

        # 保存
        elif self.mode == "Save":
            save()
        # 読み込み
        elif self.mode == "Load":
            load()
        # コマンドをインスタンスに
        elif self.mode == "Recorder_to_Instance":
            recorder_to_instance()
        # インスタンスをコマンドに
        elif self.mode == "Instance_to_Recorder":
            instance_to_recorder()
        # 削除
        elif self.mode == "I_Remove":
            i_remove()
        # 上へ
        elif self.mode == "I_Up":
            i_move("Up")
        # 下へ
        elif self.mode == "I_Down":
            i_move("Down")
        # インスタンスのリネーム
        elif self.mode == "Rename":
            rename_instance()
        # インスタンスを実行
        else:
            execute_instance(CR_Prop.Instance_Name.index(self.mode))

        bpy.context.area.tag_redraw()
        return {"FINISHED"}  # UI系の関数の最後には必ず付ける


def recent_switch(mode:str):
    if mode == "Standard":
        bpy.app.debug_wm = 0
    else:
        bpy.app.debug_wm = 1
    CR_PT_List.Bool_Recent = mode


# ==============================================================
# レイアウト
# -------------------------------------------------------------------------------------------
# メニュー
class CR_PT_List(bpy.types.Panel):
    bl_region_type = "UI"  # メニューを表示するリージョン
    bl_category = "CommandRecorder"  # メニュータブのヘッダー名
    bl_label = "CommandRecorder"  # タイトル
    # 変数の宣言
    # -------------------------------------------------------------------------------------------
    Bool_Record = 0
    Bool_Recent = ""

    # レイアウト
    # -------------------------------------------------------------------------------------------
    def draw_header(self, context):
        self.layout.label(text="", icon="REC")

    # メニューの描画処理
    def draw(self, context):
        scene = bpy.context.scene
        # -------------------------------------------------------------------------------------------
        layout = self.layout
        box = layout.box()
        box_row = box.row()
        box_row.label(text="", icon="SETTINGS")
        if len(CR_("List", 0)):
            box_row.prop(CR_("List", 0)[CR_("Index", 0)], "name", text="")
        box_row = box.row()
        col = box_row.column()
        col.template_list(
            "CR_List_Selector",
            "",
            scene.CR_Var,
            "List_Command_000",
            scene.CR_Var,
            "List_Index_000",
            rows=4,
        )
        col = box_row.column()
        col.operator(CR_OT_Selector.bl_idname, text="", icon="ADD").mode = "Add"
        col.operator(CR_OT_Selector.bl_idname, text="", icon="REMOVE").mode = "Remove"
        col.operator(CR_OT_Selector.bl_idname, text="", icon="TRIA_UP").mode = "Up"
        col.operator(CR_OT_Selector.bl_idname, text="", icon="TRIA_DOWN").mode = "Down"
        #
        if len(CR_("List", 0)):
            box_row = box.row()
            box_row.label(text="", icon="TEXT")
            if len(CR_("List", CR_("Index", 0) + 1)):
                box_row.prop(
                    CR_("List", CR_("Index", 0) + 1)[CR_("Index", CR_("Index", 0) + 1)],
                    "name",
                    text="",
                )
            box_row = box.row()
            col = box_row.column()
            col.template_list(
                "CR_List_Command",
                "",
                scene.CR_Var,
                "List_Command_{0:03d}".format(CR_("Index", 0) + 1),
                scene.CR_Var,
                "List_Index_{0:03d}".format(CR_("Index", 0) + 1),
                rows=4,
            )
            col = box_row.column()
            if CR_PT_List.Bool_Record:
                col.operator(
                    CR_OT_Command.bl_idname, text="", icon="PAUSE"
                ).mode = "Record_Stop"
            else:
                col.operator(
                    CR_OT_Command.bl_idname, text="", icon="REC"
                ).mode = "Record_Start"
                col.operator(Command_OT_Add.bl_idname, text="", icon="ADD")
                col.operator(
                    CR_OT_Command.bl_idname, text="", icon="REMOVE"
                ).mode = "Remove"
                col.operator(
                    CR_OT_Command.bl_idname, text="", icon="TRIA_UP"
                ).mode = "Up"
                col.operator(
                    CR_OT_Command.bl_idname, text="", icon="TRIA_DOWN"
                ).mode = "Down"
            if len(CR_("List", CR_("Index", 0) + 1)):
                box.operator(Command_OT_Play.bl_idname, text="Play")
                box.operator(
                    CR_OT_Instance.bl_idname, text="Recorder to Button"
                ).mode = "Recorder_to_Instance"
                box.operator(CR_OT_Command.bl_idname, text="Clear").mode = "Clear"
        box = layout.box()
        box.label(text="Options", icon="PRESET_NEW")
        # box_row = box.row()
        # box_row.label(text = 'Target')
        # box_row.prop(scene.CR_Var, 'Target_Switch' ,expand = 1)
        box_row = box.row()
        box_row.label(text="History")
        box_row.prop(scene.CR_Var, "Recent_Switch", expand=1)
        if not (CR_PT_List.Bool_Recent == scene.CR_Var.Recent_Switch):
            recent_switch(scene.CR_Var.Recent_Switch)
        box_row = box.row()
        box_row.label(text="Ignore Undo")
        box_row.prop(scene.CR_Var, "IgnoreUndo", toggle=1, text="Ignore")


class CR_PT_Instance(bpy.types.Panel):
    bl_space_type = "VIEW_3D"  # メニューを表示するエリア
    bl_region_type = "UI"  # メニューを表示するリージョン
    bl_category = "CommandRecorder"  # メニュータブのヘッダー名
    bl_label = "CommandButton"  # タイトル
    # 変数の宣言
    # -------------------------------------------------------------------------------------------
    StartUp = 0
    SelectedInctance = ""
    # レイアウト
    # -------------------------------------------------------------------------------------------
    def draw_header(self, context):
        self.layout.label(text="", icon="PREFERENCES")

    # メニューの描画処理
    def draw(self, context):
        if CR_PT_Instance.StartUp == 0:
            load()
            CR_PT_Instance.StartUp = 1
        scene = bpy.context.scene
        # -------------------------------------------------------------------------------------------
        layout = self.layout
        #

        box = layout.box()
        box.operator(
            CR_OT_Instance.bl_idname, text="Button to Recorder"
        ).mode = "Instance_to_Recorder"
        box_split = box.split(factor=0.2)
        box_col = box_split.column()
        box_col.prop(scene.CR_Var, "Instance_Index", expand=1)
        box_col = box_split.column()
        box_col.scale_y = 0.9493
        for Num_Loop in range(len(CR_Prop.Instance_Name)):
            box_col.operator(
                CR_OT_Instance.bl_idname, text=CR_Prop.Instance_Name[Num_Loop]
            ).mode = CR_Prop.Instance_Name[Num_Loop]
        if len(CR_Prop.Instance_Name):
            box_row = box.row()
            box_row.operator(
                CR_OT_Instance.bl_idname, text="", icon="REMOVE"
            ).mode = "I_Remove"
            box_row.operator(
                CR_OT_Instance.bl_idname, text="", icon="TRIA_UP"
            ).mode = "I_Up"
            box_row.operator(
                CR_OT_Instance.bl_idname, text="", icon="TRIA_DOWN"
            ).mode = "I_Down"
            box_row.prop(scene.CR_Var, "Rename", text="")
            box_row.operator(CR_OT_Instance.bl_idname, text="Rename").mode = "Rename"
        box = layout.box()
        box.operator(CR_OT_Instance.bl_idname, text="Save to File").mode = "Save"
        box.operator(CR_OT_Instance.bl_idname, text="Load from File").mode = "Load"


class CR_List_PT_VIEW_3D(CR_PT_List):
    bl_space_type = "VIEW_3D"  # メニューを表示するエリア


class CR_PT_Instance_VIEW_3D(CR_PT_Instance):
    bl_space_type = "VIEW_3D"  # メニューを表示するエリア


class CR_List_PT_IMAGE_EDITOR(CR_PT_List):
    bl_space_type = "IMAGE_EDITOR"


class CR_PT_Instance_IMAGE_EDITOR(CR_PT_Instance):
    bl_space_type = "IMAGE_EDITOR"


def Num_Instance_Updater(self, context):
    items = []
    for Num_Loop in range(len(CR_Prop.Instance_Name)):
        items.append((str(Num_Loop), "{0}".format(Num_Loop + 1), ""))
    return items


class CR_Prop(PropertyGroup):  # 何かとプロパティを収納
    Rename: StringProperty()  # CR_Var.name

    Instance_Name = []
    Instance_Command = []

    Instance_Index: EnumProperty(items=Num_Instance_Updater)
    # コマンド切り替え
    Target_Switch: EnumProperty(
        items=[("Once", "Once", ""), ("Each", "Each", ""),]
    )
    # 履歴の詳細
    Recent_Switch: EnumProperty(
        items=[("Standard", "Standard", ""), ("Extend", "Extend", ""),]
    )

    IgnoreUndo: BoolProperty(
        default=True, description="all records and changes are unaffected by undo"
    )

    Temp_Command = []
    Temp_Num = 0
    for Num_Loop in range(256):
        exec("List_Index_{0:03d} : IntProperty(default = 0)".format(Num_Loop))
        exec(
            "List_Command_{0:03d} : CollectionProperty(type = CR_OT_String)".format(
                Num_Loop
            )
        )

    # ==============================================================
    # (キーが押されたときに実行する bpy.types.Operator のbl_idname, キー, イベント, Ctrlキー, Altキー, Shiftキー)
    addon_keymaps = []
    key_assign_list = [
        (Command_OT_Add.bl_idname, "COMMA", "PRESS", False, False, True),
        (Command_OT_Play.bl_idname, "PERIOD", "PRESS", False, False, True),
        (CR_OT_Selector_Up.bl_idname, "WHEELUPMOUSE", "PRESS", False, False, True),
        (CR_OT_Selector_Down.bl_idname, "WHEELDOWNMOUSE", "PRESS", False, False, True),
    ]


# ==============================================================
# プロパティの宣言
# -------------------------------------------------------------------------------------------
def initialize_props():  # プロパティをセットする関数
    bpy.types.Scene.CR_Var = bpy.props.PointerProperty(type=CR_Prop)
    if bpy.context.window_manager.keyconfigs.addon:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            name="Window", space_type="EMPTY"
        )  # Nullとして登録
        CR_Prop.addon_keymaps.append(km)
        for (idname, key, event, ctrl, alt, shift) in CR_Prop.key_assign_list:
            kmi = km.keymap_items.new(
                idname, key, event, ctrl=ctrl, alt=alt, shift=shift
            )  # ショートカットキーの登録


def clear_props():
    del bpy.types.Scene.CR_Var
    for km in CR_Prop.addon_keymaps:
        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)
    CR_Prop.addon_keymaps.clear()


# ==============================================================
# Blenderへ登録
# -------------------------------------------------------------------------------------------
# 使用されているクラスを格納
Class_List = [
    CR_OT_String,
    CR_Prop,
    CR_List_Selector,
    CR_OT_Selector,
    CR_OT_Selector_Up,
    CR_OT_Selector_Down,
    CR_List_Command,
    Command_OT_Play,
    Command_OT_Add,
    CR_OT_Command,
    CR_List_Instance,
    CR_OT_Instance,
    CR_List_PT_VIEW_3D,
    CR_PT_Instance_VIEW_3D,
    CR_List_PT_IMAGE_EDITOR,
    CR_PT_Instance_IMAGE_EDITOR,
]
