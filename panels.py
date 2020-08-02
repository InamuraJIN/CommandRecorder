import bpy

from typing import List

from .utils.macro import list_global_macro_names, list_local_macro_names
from .operators import (
    AddLocalMacroOperator,
    MoveMacroToGlobalOperator,
    MoveMacroToLocalOperator,
    PlayCommandOperator,
    RecordCommandOperator,
    RemoveGlobalMacroOperator,
    RemoveLocalMacroOperator,
    RenameGlobalMacroOperator,
    RenameLocalMacroOperator,
    SelectGlobalMacroOperator,
    SelectLocalMacroOperator,
    TestOpOperator,
)
from .state import state


"""

■グローバルマクロ一覧パネル
Storageに保存する、グローバルに使用するマクロ。
[番号ボタン, コマンドボタン]
で表示。
・削除、上に移動、下に移動

■コマンド移動パネル
・グローバルに移動ボタン
・ローカルに移動 ボタン
番号ボタンで選択されているアイテムを操作

■ローカルマクロ（ファイル固有マクロ）一覧パネル
ファイルにテキストとして保存するマクロの一覧。
[番号ボタン, コマンドボタン]
で表示。デフォルトショートカットがついている。
・追加、削除、複製、上に移動、下に移動

■ローカルマクロ編集パネル
番号で選択されているローカルマクロを編集する。
リストの上下などで順番を変更したりする
・Recボタン
・マクロ名
・オペレーションリスト編集

"""


class CommandRecorderPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CommandRecorder"


###############################################################


class CommandRecorder_MainPanel(CommandRecorderPanel, bpy.types.Panel):
    bl_label = "CommandRecorder"
    bl_idname = "CommandRecorderMainPanel"

    def draw(self, context):
        layout = self.layout
        # layout.label(text="MainPanel")

        pass


###############################################################


# type = "global" | "local"
def layout_macros(layout, type: str, names: List[str], active_name: str):
    for name in names:
        sub_layout = layout.row(align=True)

        col_selection = sub_layout.column(align=True)
        col_player = sub_layout.column(align=True)

        selection_icon = "RADIOBUT_OFF"
        if active_name == name:
            selection_icon = "RADIOBUT_ON"

        if type == "global":
            select_operator = col_selection.operator(
                SelectGlobalMacroOperator.bl_idname, text="", icon=selection_icon
            )
        else:
            select_operator = col_selection.operator(
                SelectLocalMacroOperator.bl_idname, text="", icon=selection_icon
            )

        select_operator.name = name

        operator = col_player.operator(
            PlayCommandOperator.bl_idname, text=name, icon="PLAY"
        )
        operator.type = type
        operator.name = name


class CommandRecorder_GlobalMacroListPanel(CommandRecorderPanel, bpy.types.Panel):
    bl_label = "Global Macros"
    bl_parent_id = CommandRecorder_MainPanel.bl_idname

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        layout_macros(
            box, "global", list_global_macro_names(), state["global_macro_active_name"]
        )

        managing_row = layout.row()
        managing_row.operator(RenameGlobalMacroOperator.bl_idname)
        managing_row.operator(
            RemoveGlobalMacroOperator.bl_idname, text="", icon="TRASH"
        )

        moving_row = layout.row()
        moving_row.operator(MoveMacroToLocalOperator.bl_idname, icon="TRIA_DOWN")


class CommandRecorder_LocalMacroListPanel(CommandRecorderPanel, bpy.types.Panel):
    bl_label = "Local Macros"
    bl_parent_id = CommandRecorder_MainPanel.bl_idname

    def draw(self, context):
        layout = self.layout

        layout.operator(MoveMacroToGlobalOperator.bl_idname, icon="TRIA_UP")

        layout = self.layout
        box = layout.box()

        layout_macros(
            box, "local", list_local_macro_names(), state["local_macro_active_name"]
        )

        managing_row = layout.row()
        managing_row.operator(AddLocalMacroOperator.bl_idname, text="", icon="ADD")

        rec_icon = "REC" if not RecordCommandOperator.state_running else "PAUSE"
        rec_text = "Rec" if not RecordCommandOperator.state_running else "stop Rec"
        managing_row.operator(
            RecordCommandOperator.bl_idname, text=rec_text, icon=rec_icon
        )

        managing_row.operator(RenameLocalMacroOperator.bl_idname)
        managing_row.operator(RemoveLocalMacroOperator.bl_idname, text="", icon="TRASH")


class CommandRecorder_LocalMacroEditorPanel(CommandRecorderPanel, bpy.types.Panel):
    bl_label = "Local Macro Editor"
    bl_parent_id = CommandRecorder_MainPanel.bl_idname

    def draw(self, context):
        layout = self.layout


###############################################################
class CommandRecorder_MiscPanel(CommandRecorderPanel, bpy.types.Panel):
    bl_label = "develop"
    bl_parent_id = CommandRecorder_MainPanel.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.label(text="test")
        layout.operator(TestOpOperator.bl_idname)
        layout.operator(RecordCommandOperator.bl_idname)
        layout.operator(PlayCommandOperator.bl_idname)


classes = [
    CommandRecorder_MainPanel,
    CommandRecorder_GlobalMacroListPanel,
    CommandRecorder_LocalMacroListPanel,
    CommandRecorder_LocalMacroEditorPanel,
    # CommandRecorder_MiscPanel,
]

