#==============================================================
#スタートアップ
#-------------------------------------------------------------------------------------------
import bpy #Blender内部のデータ構造にアクセスするために必要
from bpy.app.handlers import persistent
import os
import shutil
import json
from json.decoder import JSONDecodeError
import zipfile

from bpy.props import\
(#プロパティを使用するために必要
StringProperty,
BoolProperty,
IntProperty,
FloatProperty,
EnumProperty,
PointerProperty,
CollectionProperty
)
from bpy.types import\
(
Panel,
UIList,
Operator,
PropertyGroup
)


from . import DefineCommon as Common
from bpy_extras.io_utils import ImportHelper, ExportHelper

def TempNameUpdate(self, context):
    TempUpdate()

class CR_OT_String(PropertyGroup):#リストデータを保持するためのプロパティグループを作成
    cname : StringProperty(default='', update= TempNameUpdate) #CR_Var.name

class CR_List_Selector(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.cname)
class CR_List_Command(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.cname)
class CR_List_Instance(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.cname)


#-------------------------------------------------------------------------------------------

def CR_(Data , Num):
    scene = bpy.context.scene
    if Data == 'List' :
        return eval('scene.CR_Var.List_Command_{0:03d}'.format(Num))
    elif Data == 'Index' :
        return eval('scene.CR_Var.List_Index_{0:03d}'.format(Num))
    else :
        exec('scene.CR_Var.List_Index_{0:03d} = {1}'.format(Num,Data))

def Get_Recent(Return_Bool):#操作履歴にアクセス
    #remove other Recent Reports
    reports = \
    [
    bpy.data.texts.remove(t, do_unlink=True)
    for t in bpy.data.texts
        if t.name.startswith('Recent Reports')
    ]
    # make a report
    win = bpy.context.window_manager.windows[0]
    area = win.screen.areas[0]
    area_type = area.type
    area.type = 'INFO'
    override = bpy.context.copy()
    override['window'] = win
    override['screen'] = win.screen
    override['area'] = win.screen.areas[0]
    bpy.ops.info.select_all(override, action='SELECT')
    bpy.ops.info.report_copy(override)
    area.type = area_type
    clipboard = bpy.context.window_manager.clipboard
    bpy.data.texts.new('Recent Reports')
    bpy.data.texts['Recent Reports'].write(clipboard)
    # print the report
    if Return_Bool == 'Reports_All':
        return bpy.data.texts['Recent Reports'].lines#操作履歴全ての行
    elif Return_Bool == 'Reports_Length':
        return len(bpy.data.texts['Recent Reports'].lines)#操作履歴の要素数

def Record(Num, Mode):
    Recent = Get_Recent('Reports_All')
    if Mode == 'Start':
        CR_PT_Panel.Bool_Record = 1
        CR_Prop.Temp_Num = len(Recent)
    else:
        CR_PT_Panel.Bool_Record = 0
        for i in range (CR_Prop.Temp_Num, len(Recent)):
            TempText = Recent[i-1].body
            if TempText.count('bpy'):
                Item = CR_('List', Num).add()
                Item.cname = TempText[TempText.find('bpy'):]

def CreateTempFile():
    tpath = bpy.app.tempdir + "temp.json"
    if not os.path.exists(tpath):
        print(tpath)
        with open(tpath, 'w', encoding='utf8') as tempfile:
            json.dump({"0":[]}, tempfile)
    return tpath

def TempSave(Num):  # write new command to temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:   
        data = json.load(tempfile)
        data.update({str(Num):[]})
        data["0"].append(CR_('List', 0)[Num - 1]['cname'])
        tempfile.seek(0)
        json.dump(data, tempfile)

def TempUpdate(): # update all commands in temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        data = {}
        for cmd in range(len(CR_('List', 0)) + 1):
            data.update({str(cmd):[i.cname for i in CR_('List', cmd)]})
        json.dump(data, tempfile)

def TempUpdateCommand(Key): # update one command in temp.json file
    tpath = CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        data[str(Key)] = [i.cname for i in CR_('List', int(Key))]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

@persistent
def TempLoad(dummy): # load commands after undo
    tpath = bpy.app.tempdir + "temp.json"
    if bpy.context.scene.CR_Var.IgnoreUndo and os.path.exists(tpath):
        with open(tpath, 'r', encoding='utf8') as tempfile:
            data = json.load(tempfile)
        command = CR_('List', 0)
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.cname = data["0"][i - 1]
            record = CR_('List', i)
            record.clear()
            for j in range(len(data[keys[i]])):
                Item = record.add()
                Item.cname = data[keys[i]][j]

UndoRedoStack = []

def GetCommand(index):
    return eval('bpy.context.scene.CR_Var.List_Command_{0:03d}'.format(index))

@persistent
def SaveUndoStep(dummy):
    All = []
    l = []
    l.append([i.cname for i in list(GetCommand(0))])
    for x in range(1, len(l[0]) + 1):
        l.append([ i.cname for i in list(GetCommand(x))])
    UndoRedoStack.append(l)

@persistent
def GetRedoStep(dummy):
    command = CR_('List', 0)
    command.clear()
    l = UndoRedoStack[len(UndoRedoStack) - 1]
    for i in range(1, len(l[0]) + 1):
        item = command.add()
        item.cname = l[0][i - 1]
        record = CR_('List', i)
        record.clear()
        for j in range(len(l[i])):
            item = record.add()
            item.cname = l[i][j]
    UndoRedoStack.pop()


def Add(Num):
    Recent = Get_Recent('Reports_All')
    if Num or len(CR_('List', 0)) < 250:
        Item = CR_('List', Num).add()
        if Num:
            if Recent[-2].body.count('bpy'):
                Name_Temp = Recent[-2].body
                Item.cname = Name_Temp[Name_Temp.find('bpy'):]
            else:
                Name_Temp = Recent[-3].body
                Item.cname = Name_Temp[Name_Temp.find('bpy'):]
        else:
            Item.cname = 'Untitled_{0:03d}'.format(len(CR_('List', Num)))
        CR_( len(CR_('List',Num))-1, Num )

def Remove(Num):
    if not Num:
        for Num_Loop in range(CR_('Index',0)+1 , len(CR_('List',0))+1) :
            CR_('List',Num_Loop).clear()
            for Num_Command in range(len(CR_('List',Num_Loop+1))) :
                Item = CR_('List',Num_Loop).add()
                Item.cname = CR_('List',Num_Loop+1)[Num_Command].cname
            CR_(CR_('Index',Num_Loop+1),Num_Loop)
    if len(CR_('List',Num)):
        CR_('List',Num).remove(CR_('Index',Num))
        if len(CR_('List',Num)) - 1 < CR_('Index',Num):
            CR_(len(CR_('List',Num))-1,Num)
            if CR_('Index',Num) < 0:
                CR_(0,Num)


def Move(Num , Mode) :
    index1 = CR_('Index',Num)
    if Mode == 'Up' :
        index2 = CR_('Index',Num) - 1
    else :
        index2 = CR_('Index',Num) + 1
    LengthTemp = len(CR_('List',Num))
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 <LengthTemp):
        CR_('List',Num).move(index1, index2)
        CR_(index2 , Num)

        #コマンドの入れ替え処理
        if not Num :
            index1 += 1
            index2 += 1
            CR_('List',254).clear()
            #254にIndex2を逃がす
            for Num_Command in CR_('List',index2) :
                Item = CR_('List',254).add()
                Item.cname = Num_Command.cname
            CR_(CR_('Index',index2),254)
            CR_('List',index2).clear()
            #Index1からIndex2へ
            for Num_Command in CR_('List',index1) :
                Item = CR_('List',index2).add()
                Item.cname = Num_Command.cname
            CR_(CR_('Index',index1),index2)
            CR_('List',index1).clear()
            #254からIndex1へ
            for Num_Command in CR_('List',254) :
                Item = CR_('List',index1).add()
                Item.cname = Num_Command.cname
            CR_(CR_('Index',254),index1)
            CR_('List',254).clear()

def Select_Command(Mode):
    currentIndex = CR_('Index',0)
    listlen = len(CR_('List',0)) - 1
    if Mode == 'Up':
        if currentIndex == 0:
            bpy.context.scene.CR_Var.List_Index_000 = listlen
        else:
            bpy.context.scene.CR_Var.List_Index_000 = currentIndex - 1
    else:
        if currentIndex == listlen:
            bpy.context.scene.CR_Var.List_Index_000 = 0
        else:
            bpy.context.scene.CR_Var.List_Index_000 = currentIndex + 1

def Play(Commands) :
    scene = bpy.context.scene
    for Command in Commands :
        if type(Command) == str :
            exec(Command)
        else :
            exec(Command.cname)

def Clear(Num) :
    CR_('List',Num).clear()

class CR_OT_Selector(Operator):
    bl_idname = 'cr_selector.button'#大文字禁止
    bl_label = 'Button_Selector'#メニューに登録される名前
    #bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    Mode : bpy.props.StringProperty(default='')
    def execute(self, context):
        scene = bpy.context.scene
        #追加
        if self.Mode == 'Add' :
            Add(0)
            if scene.CR_Var.IgnoreUndo:
                TempSave(CR_('Index',0) + 1)
        #削除
        elif self.Mode == 'Remove' :
            Remove(0)
            if scene.CR_Var.IgnoreUndo:
                TempUpdate()
        #上へ
        elif self.Mode == 'Up' :
            Move(0 , 'Up')
            if scene.CR_Var.IgnoreUndo:
                TempUpdate()
        #下へ
        elif self.Mode == 'Down' :
            Move(0 , 'Down')
            if scene.CR_Var.IgnoreUndo:
                TempUpdate()
        bpy.context.area.tag_redraw()
        return{'FINISHED'}#UI系の関数の最後には必ず付ける

class CR_OT_Selector_Up(Operator):
    bl_idname = 'cr_selector_up.button'
    bl_label = 'Command_OT_Selection_Up'
    #bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        Select_Command('Up')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}

class CR_OT_Selector_Down(Operator):
    bl_idname = 'cr_selector_down.button'
    bl_label = 'Command_OT_Selection_Down'
    #bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        Select_Command('Down')
        bpy.context.area.tag_redraw()
        return{'FINISHED'}

class Command_OT_Play(Operator):
    bl_idname = 'cr_commandplay.button'#大文字禁止
    bl_label = 'Command_OT_Play'#メニューに登録される名前
    bl_options = {'REGISTER', 'UNDO'}#アンドゥ履歴に登録
    def execute(self, context):
        #コマンドを実行
        Play(CR_('List',CR_('Index',0)+1))
        return{'FINISHED'}#UI系の関数の最後には必ず付ける

class Command_OT_Add(Operator):
    bl_idname = 'cr_commandadd.button'#大文字禁止
    bl_label = 'Command_OT_Add'#メニューに登録される名前
    #bl_options = {'REGISTER', 'UNDO'}#アンドゥ履歴に登録
    def execute(self, context):
        #コマンドを実行
        Add(CR_('Index',0)+1)
        if bpy.context.scene.CR_Var.IgnoreUndo:
            TempUpdateCommand(CR_('Index',0)+1)
        bpy.context.area.tag_redraw()
        return{'FINISHED'}#UI系の関数の最後には必ず付ける

class CR_OT_Command(Operator):
    bl_idname = 'cr_command.button'#大文字禁止
    bl_label = 'Button_Command'#メニューに登録される名前
    #bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    Mode : bpy.props.StringProperty(default='')
    def execute(self, context):
        scene = bpy.context.scene
        #録画を開始
        if self.Mode == 'Record_Start' :
            Record(CR_('Index',0)+1 , 'Start')
        #録画を終了
        elif self.Mode == 'Record_Stop' :
            Record(CR_('Index',0)+1 , 'Stop')
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)
        #追加
        elif self.Mode == 'Add' :
            Add(CR_('Index',0)+1)
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)
        #削除
        elif self.Mode == 'Remove' :
            Remove(CR_('Index',0)+1)
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)
        #上へ
        elif self.Mode == 'Up' :
            Move(CR_('Index',0)+1 , 'Up')
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)
        #下へ
        elif self.Mode == 'Down' :
            Move(CR_('Index',0)+1 , 'Down')
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)
        #リストをクリア
        elif self.Mode == 'Clear' :
            Clear(CR_('Index',0)+1)
            if scene.CR_Var.IgnoreUndo:
                TempUpdateCommand(CR_('Index',0)+1)

        bpy.context.area.tag_redraw()
        return{'FINISHED'}#UI系の関数の最後には必ず付ける

def Save():
    for savedfolder in os.listdir(path):
        folderpath = path + "/" + savedfolder
        for savedfile in os.listdir(folderpath):
            os.remove(folderpath + "/" + savedfile)
        os.rmdir(folderpath)
    for cat in bpy.context.scene.cr_categories:
        panelpath = path + "/" + f"{GetPanelIndex(cat)}~" + cat.pn_name
        os.mkdir(panelpath)
        start = cat.Instance_Start
        for cmd_i in range(start, start + cat.Instance_length):
            with open(panelpath + "/" + f"{cmd_i - start}~" + CR_Prop.Instance_Name[cmd_i] + ".txt", 'w', encoding='utf8') as cmd_file:
                for cmd in CR_Prop.Instance_Command[cmd_i]:
                    cmd_file.write(cmd + "\n")

def Load():
    print('------------------Load-----------------')
    scene = bpy.context.scene
    scene.cr_categories.clear()
    scene.cr_enum.clear()
    CR_Prop.Instance_Name.clear()
    CR_Prop.Instance_Command.clear()
    for folder in os.listdir(path):
        folderpath = path + "/" + folder
        if os.path.isdir(folderpath):
            textfiles = os.listdir(folderpath)
            new = scene.cr_categories.add()
            name = "".join(folder.split('~')[1:])
            new.name = name
            new.pn_name = name
            new.pn_show = True
            new.Instance_Start = len(CR_Prop.Instance_Name)
            new.Instance_length = len(textfiles)
            sortedtxt = [None] * len(textfiles)
            for txt in textfiles:
                sortedtxt[int(os.path.splitext(txt)[0].split('~')[0])] = txt #remove the .txtending, join to string again, get the index ''.join(txt.split('.')[:-1])
            for i in range(len(sortedtxt)):
                txt = sortedtxt[i]
                new_e = scene.cr_enum.add()
                e_index = len(scene.cr_enum) - 1
                new_e.name = str(e_index)
                new_e.Index = e_index
                CR_Prop.Instance_Name.append("".join(os.path.splitext(txt)[0].split('~')[1:]))
                CmdList = []
                with open(folderpath + "/" + txt, 'r', encoding='utf8') as text:
                    for line in text.readlines():
                        CmdList.append(line.strip())
                CR_Prop.Instance_Command.append(CmdList)
    SetEnumIndex()


def Recorder_to_Instance(panel):
    scene = bpy.context.scene
    i = panel.Instance_Start +  panel.Instance_length
    CR_Prop.Instance_Name.insert(i, CR_('List',0)[CR_('Index',0)].cname)
    Temp_Command = []
    for Command in CR_('List',CR_('Index',0)+1):
        Temp_Command.append(Command.cname)
    CR_Prop.Instance_Command.insert(i, Temp_Command)
    panel.Instance_length += 1
    new_e = scene.cr_enum.add()
    e_index = len(scene.cr_enum) - 1
    new_e.name = str(e_index)
    new_e.Index = e_index
    p_i = GetPanelIndex(panel)
    categories = scene.cr_categories
    if p_i < len(categories):
        for cat in categories[ p_i + 1: ]:
            cat.Instance_Start += 1

def Instance_to_Recorder():
    scene = bpy.context.scene
    Item = CR_('List' , 0 ).add()
    Item.cname = CR_Prop.Instance_Name[scene.CR_Var.Instance_Index]
    for Command in CR_Prop.Instance_Command[scene.CR_Var.Instance_Index] :
        Item = CR_('List' , len(CR_('List',0)) ).add()
        Item.cname = Command
    CR_( len(CR_('List',0))-1 , 0 )

def Execute_Instance(Num):
    Play(CR_Prop.Instance_Command[Num])

def Rename_Instance():
    scene = bpy.context.scene
    CR_Prop.Instance_Name[scene.CR_Var.Instance_Index] = scene.CR_Var.Rename

def I_Remove():
    scene = bpy.context.scene
    if len(CR_Prop.Instance_Name) :
        Index = scene.CR_Var.Instance_Index
        CR_Prop.Instance_Name.pop(Index)
        CR_Prop.Instance_Command.pop(Index)
        scene.cr_enum.remove(len(scene.cr_enum) - 1)
        categories = scene.cr_categories
        for cat in categories:
            if Index >= cat.Instance_Start and Index < cat.Instance_Start + cat.Instance_length:
                cat.Instance_length -= 1
                p_i = GetPanelIndex(cat)
                if p_i < len(categories):
                    for cat in categories[ p_i + 1: ]:
                        cat.Instance_Start -= 1
                break
        if len(CR_Prop.Instance_Name) and len(CR_Prop.Instance_Name)-1 < Index :
            scene.CR_Var.Instance_Index = len(CR_Prop.Instance_Name)-1
    SetEnumIndex()

def I_Move(Mode):
    scene = bpy.context.scene
    index1 = scene.CR_Var.Instance_Index
    if Mode == 'Up' :
        index2 = scene.CR_Var.Instance_Index - 1
    else :
        index2 = scene.CR_Var.Instance_Index + 1
    LengthTemp = len(CR_Prop.Instance_Name)
    if (2 <= LengthTemp) and (0 <= index1 < LengthTemp) and (0 <= index2 <LengthTemp):
        CR_Prop.Instance_Name[index1] , CR_Prop.Instance_Name[index2] = CR_Prop.Instance_Name[index2] , CR_Prop.Instance_Name[index1]
        CR_Prop.Instance_Command[index1] , CR_Prop.Instance_Command[index2] = CR_Prop.Instance_Command[index2] , CR_Prop.Instance_Command[index1]
        scene.cr_enum[index2].Value = True

class CR_OT_Instance(Operator):
    bl_idname = 'cr_instance.button'#大文字禁止
    bl_label = 'Button_Instance'#メニューに登録される名前
    #bl_options = {'REGISTER', 'UNDO'} # 処理の属性
    Mode : bpy.props.StringProperty(default='')
    def execute(self, context):
        #追加
        if self.Mode == 'Add' :
            Add(255)
        #削除
        elif self.Mode == 'Remove' :
            Remove(255)
        #上へ
        elif self.Mode == 'Up' :
            Up(255)
        #下へ
        elif self.Mode == 'Down' :
            Down(255)

        #保存
        elif self.Mode == 'Save' :
            Save()
        #読み込み
        elif self.Mode == 'Load' :
            Load()
            TempSaveCats()
        #コマンドをインスタンスに
        elif self.Mode == 'Instance_to_Recorder' :
            Instance_to_Recorder()
            TempUpdate()
        #削除
        elif self.Mode == 'I_Remove' :
            I_Remove()
            TempSaveCats()
        #上へ
        elif self.Mode == 'I_Up' :
            I_Move('Up')
            TempSaveCats()
        #下へ
        elif self.Mode == 'I_Down' :
            I_Move('Down')
            TempSaveCats()
        #インスタンスのリネーム
        elif self.Mode == 'Rename' :
            Rename_Instance()
            TempSaveCats()
        #インスタンスを実行
        else :
            Execute_Instance(int(self.Mode))

        bpy.context.area.tag_redraw()
        return{'FINISHED'}#UI系の関数の最後には必ず付ける
        
class CR_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'# メニューを表示するエリア
    bl_region_type = 'UI'# メニューを表示するリージョン
    bl_category = 'CommandRecorder'# メニュータブのヘッダー名
    bl_label = 'CommandButton'# タイトル
    #変数の宣言
    #-------------------------------------------------------------------------------------------
    SelectedInctance = ''
    Bool_Record = 0
    Bool_Recent = ''
    #レイアウト
    #-------------------------------------------------------------------------------------------
    def draw_header(self, context):
        self.layout.label(text = '', icon = 'REC')
    #メニューの描画処理
    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        layout.prop(scene.CR_Var, 'PanelType', text= scene.CR_Var.PanelType, expand= True)
        if scene.CR_Var.PanelType == "button":
            #Button --------------------------------------
            box = layout.box()
            row = box.row(align= True)
            row.operator(CR_OT_Instance.bl_idname , text='Button to Recorder' ).Mode = 'Instance_to_Recorder'
            row.prop(scene.CR_Var, 'ShowMenu', text= "", icon= 'COLLAPSEMENU')
            col = box.column(align= True)
            if scene.CR_Var.ShowMenu:
                col.operator(CR_OT_Instance.bl_idname , text='Save to File' ).Mode = 'Save'
                col.operator(CR_OT_Instance.bl_idname , text='Load from File' ).Mode = 'Load'
                col.operator(AddCategory.bl_idname, text= "Add from File").Mode = 'AddFromFile'
                col = box.column(align= True)
                col.operator(ImportButton.bl_idname, text= 'Import')
                col.operator(ExportButton.bl_idname, text= 'Export')
            else:
                col.operator(CR_OT_Instance.bl_idname , text='Save to File' ).Mode = 'Save'
            row = box.row().split(factor= 0.4)
            row.label(text= 'Category')
            row2 = row.row(align= True)
            row2.scale_x = 1.1737
            row2.operator(AddCategory.bl_idname, text= '', icon= 'ADD').Mode = 'Add'
            row2.operator(AddCategory.bl_idname, text= '', icon= 'TRASH').Mode = 'Delet'
            row2.operator(AddCategory.bl_idname, text= '', icon= 'GREASEPENCIL').Mode = 'Rename'
            if len(CR_Prop.Instance_Name) :
                row = box.row().split(factor= 0.4)
                row.label(text= 'Buttons')
                row2 = row.row(align= True)
                row2.operator(CR_OT_Instance.bl_idname , text='' , icon='REMOVE' ).Mode = 'I_Remove'
                row2.operator(CR_OT_Instance.bl_idname , text='' , icon='TRIA_UP' ).Mode = 'I_Up'
                row2.operator(CR_OT_Instance.bl_idname , text='' , icon='TRIA_DOWN' ).Mode = 'I_Down'
                row2.operator(AddCategory.bl_idname, text= '', icon= 'PRESET').Mode = 'Move'
            row = box.row()
            row2 = row.split(factor= 0.7)
            row2.prop(scene.CR_Var , 'Rename' , text='')
            row2.operator(CR_OT_Instance.bl_idname , text='Rename').Mode = 'Rename'
            categories = scene.cr_categories
            for cat in categories:
                box = layout.box()
                col = box.column()
                row = col.row()
                if cat.pn_show:
                    row.prop(cat, 'pn_show', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    row.prop(cat, 'pn_show', icon="TRIA_RIGHT", text= "", emboss= False)
                row.label(text= cat.pn_name)
                i = GetPanelIndex(cat)
                row2 = row.row(align= True)
                row2.operator(AddCategory.bl_idname, icon="TRIA_UP", text= "").Mode = f'Move_Up-{i}'
                row2.operator(AddCategory.bl_idname, icon="TRIA_DOWN", text="").Mode = f'Move_Down-{i}'
                if cat.pn_show:
                    split = box.split(factor=0.2)
                    col = split.column(align= True)
                    for i in range(cat.Instance_Start, cat.Instance_Start + cat.Instance_length):
                        col.prop(scene.cr_enum[i], 'Value' ,toggle = 1, text= str(i - cat.Instance_Start + 1))
                    col = split.column()
                    col.scale_y = 0.9493
                    for Num_Loop in range(cat.Instance_Start, cat.Instance_Start + cat.Instance_length):
                        col.operator(CR_OT_Instance.bl_idname , text=CR_Prop.Instance_Name[Num_Loop]).Mode = str(Num_Loop)
        else:
            #Record----------------------------------------------
            box = layout.box()
            box_row = box.row()
            box_row.label(text = '', icon = 'SETTINGS')
            if len(CR_('List',0)) :
                try:
                    box_row.prop(CR_('List',0)[CR_('Index',0)] , 'cname' , text='')
                except:
                    pass
            box_row = box.row()
            col = box_row.column()
            col.template_list('CR_List_Selector' , '' , scene.CR_Var , 'List_Command_000' , scene.CR_Var , 'List_Index_000', rows=4)
            col = box_row.column()
            col.operator(CR_OT_Selector.bl_idname , text='' , icon='ADD' ).Mode = 'Add'
            col.operator(CR_OT_Selector.bl_idname , text='' , icon='REMOVE' ).Mode = 'Remove'
            col.operator(CR_OT_Selector.bl_idname , text='' , icon='TRIA_UP' ).Mode = 'Up'
            col.operator(CR_OT_Selector.bl_idname , text='' , icon='TRIA_DOWN' ).Mode = 'Down'
            #
            if len(CR_('List',0)) :
                box2 = box.box()
                box_row = box2.row()
                if scene.CR_Var.ShowMacros:
                    box_row.prop(scene.CR_Var, 'ShowMacros', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    box_row.prop(scene.CR_Var, 'ShowMacros', icon="TRIA_RIGHT", text= "", emboss= False)
                box_row.label(text = 'Edit Macro', icon = 'TEXT')
                if scene.CR_Var.ShowMacros:
                    box_row = box2.row()
                    if len(CR_('List',CR_('Index',0)+1)) :
                        box_row.prop(CR_('List',CR_('Index',0)+1)[CR_('Index',CR_('Index',0)+1)],'cname' , text='')
                    box_row = box2.row()
                    col = box_row.column()
                    col.template_list('CR_List_Command' , '' , scene.CR_Var , 'List_Command_{0:03d}'.format(CR_('Index',0)+1) , scene.CR_Var , 'List_Index_{0:03d}'.format(CR_('Index',0)+1), rows=4)
                    col = box_row.column()
                    if not CR_PT_Panel.Bool_Record :
                        col.operator(CR_OT_Command.bl_idname , text='' , icon='TRIA_UP' ).Mode = 'Up'
                        col.operator(CR_OT_Command.bl_idname , text='' , icon='TRIA_DOWN' ).Mode = 'Down'
                row = box.row()
                if CR_PT_Panel.Bool_Record :
                    row.operator(CR_OT_Command.bl_idname , text='' , icon='PAUSE' ).Mode = 'Record_Stop'
                    row.prop(scene.CR_Var, 'IgnoreUndo', toggle = 1, text="Ignore Undo")
                else :
                    row2 = row.row(align= True)
                    row2.operator(CR_OT_Command.bl_idname , text='' , icon='REC' ).Mode = 'Record_Start'
                    row2.operator(Command_OT_Add.bl_idname , text='' , icon='ADD' )
                    row2.operator(CR_OT_Command.bl_idname , text='' , icon='REMOVE' ).Mode = 'Remove'
                    row.prop(scene.CR_Var, 'IgnoreUndo', toggle = 1, text="Ignore Undo")
                if len(CR_('List',CR_('Index',0)+1)) :
                    col = box.column(align= True)
                    col.operator(Command_OT_Play.bl_idname , text='Play' )
                    col.operator(AddCategory.bl_idname , text='Recorder to Button' ).Mode = 'ToButton'
                    col.operator(CR_OT_Command.bl_idname , text='Clear').Mode = 'Clear'

currentselected = [None]
lastselected = [None]
def UseRadioButtons(self, context):
    categories = context.scene.cr_categories
    for cat in categories:
        if not cat.pn_selected and lastselected[0] == cat and currentselected[0] == cat:
            cat.pn_selected = True
        elif cat.pn_selected and lastselected[0] != cat and currentselected[0] != cat:
            currentselected[0] = cat
            if lastselected[0] is not None:
                lastselected[0].pn_selected = False
            lastselected[0] = cat

class CategorizeProps(bpy.types.PropertyGroup):
    pn_name : StringProperty()
    pn_show : BoolProperty(default= True)
    pn_selected : BoolProperty(default= False, update= UseRadioButtons)
    Instance_Start : IntProperty(default= 0)
    Instance_length : IntProperty(default= 0)

path = os.path.dirname(__file__) + "/Storage"
#Initalize Standert Button List
@persistent
def InitSavedPanel(dummy):
    if not os.path.exists(path):
        os.mkdir(path)
    Load()

def GetPanelIndex(cat):
    return int(cat.path_from_id().split("[")[1].split("]")[0])

def SetEnumIndex():
    scene = bpy.context.scene
    if len(scene.cr_enum):
        enumIndex = scene.CR_Var.Instance_Index * (scene.CR_Var.Instance_Index < len(scene.cr_enum))
        scene.cr_enum[enumIndex].Value = True
        scene.CR_Var.Instance_Index = enumIndex

tempnotinited = [True]
@persistent
def InitTemp(dummy):
    if tempnotinited[0]:
        TempSaveCats()
        import time
        tempnotinited[0] = False
print(bpy.app.tempdir + " -------------------------------------------------------")


def CreateTempCats():
    tcatpath = bpy.app.tempdir + "tempcats.json"
    if not os.path.exists(tcatpath):
        with open(tcatpath, 'x', encoding='utf8') as tempfile:
            print(tcatpath)
    return tcatpath

def TempSaveCats():
    scene = bpy.context.scene
    tcatpath = CreateTempCats()
    with open(tcatpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        cats = []
        for cat in scene.cr_categories:
            cats.append({
                "name": cat.name,
                "pn_name": cat.pn_name,
                "pn_show": cat.pn_show,
                "Instance_Start": cat.Instance_Start,
                "Instance_length": cat.Instance_length
            })
        data = {
            "Instance_Name": CR_Prop.Instance_Name,
            "Instance_Command": CR_Prop.Instance_Command,
            "Instance_Index": scene.CR_Var.Instance_Index,
            "Categories": cats
        }
        json.dump(data, tempfile)

@persistent
def TempLoadCats(dummy):
    scene = bpy.context.scene
    tcatpath = bpy.app.tempdir + "tempcats.json"
    scene.cr_enum.clear()
    scene.cr_categories.clear()
    CR_Prop.Instance_Name.clear()
    CR_Prop.Instance_Command.clear()
    with open(tcatpath, 'r', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        CR_Prop.Instance_Name = data["Instance_Name"]
        CR_Prop.Instance_Command = data["Instance_Command"]
        index = data["Instance_Index"]
        scene.CR_Var.Instance_Index = index
        for i in range(len(CR_Prop.Instance_Name)):
            new_e = scene.cr_enum.add()
            new_e.name = str(i)
            new_e.Index = i
        scene.cr_enum[index].Value = True
        for cat in data["Categories"]:
            new = scene.cr_categories.add()
            new.name = cat["name"]
            new.pn_name = cat["pn_name"]
            new.pn_show = cat["pn_show"]
            new.Instance_Start = cat["Instance_Start"]
            new.Instance_length = cat["Instance_length"]

class AddCategory(bpy.types.Operator):
    bl_idname = "cr.add_category"
    bl_label = "Category"

    Mode : StringProperty()
    PanelName : StringProperty(name = "Category Name", default="")
    NewPanel : BoolProperty(default= False, description= "Create a new Category with all selected Buttons")

    def execute(self, context):
        categories = context.scene.cr_categories
        scene = context.scene
        if self.Mode == 'Add':
            new = scene.cr_categories.add()
            new.name = self.PanelName
            new.pn_name = self.PanelName
            new.Instance_Start = len(CR_Prop.Instance_Name)
            new.Instance_length = 0
        elif self.Mode == 'Delet':
            for cat in categories:
                if cat.pn_selected:
                    index = GetPanelIndex(cat)
                    start = cat.Instance_Start
                    for i in range(start, start + cat.Instance_length):
                        scene.cr_enum.remove(len(scene.cr_enum) - 1)
                        CR_Prop.Instance_Name.pop(start)
                        CR_Prop.Instance_Command.pop(start)
                    for nextcat in categories[index + 1 :]:
                        nextcat.Instance_Start -= cat.Instance_length
                    categories.remove(GetPanelIndex(cat))
                    SetEnumIndex()
                    break
        elif self.Mode == 'Rename':
            for cat in categories:
                if cat.pn_selected:
                    cat.name = self.PanelName
                    cat.pn_name = self.PanelName
                    break
        elif self.Mode == 'Move':
            for cat in categories:
                if cat.pn_selected:
                    Index = scene.CR_Var.Instance_Index
                    catendl = cat.Instance_Start + cat.Instance_length - 1
                    for curcat in categories:
                        if Index >= curcat.Instance_Start and Index < curcat.Instance_Start + curcat.Instance_length:
                            curcat.Instance_length -= 1
                            for nextcat in categories[GetPanelIndex(curcat) + 1 :]:
                                nextcat.Instance_Start -= 1
                            break
                    CR_Prop.Instance_Name.insert(catendl, CR_Prop.Instance_Name.pop(Index))
                    CR_Prop.Instance_Command.insert(catendl, CR_Prop.Instance_Command.pop(Index))
                    for nextcat in categories[GetPanelIndex(cat) + 1:]:
                        nextcat.Instance_Start += 1
                    cat.Instance_length += 1
                    SetEnumIndex()
                    break
        elif self.Mode == 'ToButton':
            for cat in categories:
                if cat.pn_selected:
                    Recorder_to_Instance(cat)
                    break
        elif self.Mode == 'AddFromFile':
            if self.NewPanel:
                new = scene.cr_categories.add()
                new.name = "Add from File"
                new.pn_name = "Add from File"
                new.Instance_Start = len(CR_Prop.Instance_Name)
                filedisp = scene.cr_filedisp
                for filecat in scene.cr_filecategories:
                    if filecat.pn_selected:
                        for i in range(filecat.FileDisp_Start, filecat.FileDisp_Start + filecat.FileDisp_length):
                            filedisp[i].Index = True
                for i in range(len(filedisp)):
                    if filedisp[i].Index:
                        new_e = scene.cr_enum.add()
                        e_index = len(scene.cr_enum) - 1
                        new_e.name = str(e_index)
                        new_e.Index = e_index
                        CR_Prop.Instance_Name.append(CR_Prop.FileDisp_Name[i])
                        CR_Prop.Instance_Command.append(CR_Prop.FileDisp_Command[i])
                new.Instance_length = len(CR_Prop.Instance_Name) - new.Instance_Start
                self.NewPanel = False
            else:
                for filecat in scene.cr_filecategories:
                    index = None
                    for i in range(len(categories)):
                        if categories[i].pn_name == filecat.pn_name:
                            index = i
                            break
                    if filecat.pn_selected:
                        if index is None:
                            new = scene.cr_categories.add()
                            new.name = filecat.name
                            new.pn_name = filecat.pn_name
                            new.Instance_Start = len(CR_Prop.Instance_Name)
                            new.Instance_length = filecat.FileDisp_length
                            for i in range(filecat.FileDisp_Start, filecat.FileDisp_Start + filecat.FileDisp_length):
                                new_e = scene.cr_enum.add()
                                e_index = len(scene.cr_enum) - 1
                                new_e.name = str(e_index)
                                new_e.Index = e_index
                                CR_Prop.Instance_Name.append(CR_Prop.FileDisp_Name[i])
                                CR_Prop.Instance_Command.append(CR_Prop.FileDisp_Command[i])
                        else:
                            for i_cat in range(index + 1, len(categories)):
                                categories[i_cat].Instance_Start += filecat.FileDisp_length
                            categories[index].Instance_length += filecat.FileDisp_length
                            i_start = categories[index].Instance_Start + categories[index].Instance_length - filecat.FileDisp_length
                            for i in range(i_start, categories[index].Instance_Start + categories[index].Instance_length):
                                new_e = scene.cr_enum.add()
                                e_index = len(scene.cr_enum) - 1
                                new_e.name = str(e_index)
                                new_e.Index = e_index
                                i_file = filecat.FileDisp_Start + i - i_start
                                CR_Prop.Instance_Name.insert(i , CR_Prop.FileDisp_Name[i_file])
                                CR_Prop.Instance_Command.insert(i, CR_Prop.FileDisp_Command[i_file])
                    else:
                        if index is None:
                            new = scene.cr_categories.add()
                            new.name = filecat.name
                            new.pn_name = filecat.pn_name
                            new.Instance_Start = len(CR_Prop.Instance_Name)
                            index = GetPanelIndex(new)
                        for i in range(filecat.FileDisp_Start, filecat.FileDisp_Start + filecat.FileDisp_length):
                            if scene.cr_filedisp[i].Index: # insert at i
                                new_e = scene.cr_enum.add()
                                new_e.name = str(len(scene.cr_enum) - 1)
                                i_cat = categories[index].Instance_Start + categories[index].Instance_length
                                CR_Prop.Instance_Name.insert(i_cat, CR_Prop.FileDisp_Name[i])
                                CR_Prop.Instance_Command.insert(i_cat, CR_Prop.FileDisp_Command[i])
                                categories[index].Instance_length += 1
                                for i_cat in range(index + 1, len(categories)):
                                    categories[i_cat].Instance_Start += 1
        bpy.context.area.tag_redraw()
        TempSaveCats()
        return {"FINISHED"}

    def invoke(self, context, event):
        m = self.Mode.split('-')[0]
        categories = context.scene.cr_categories
        if m == 'Move_Up':
            i = int(self.Mode.split('-')[1])
            if i - 1 >= 0:
                cat1 = categories[i]
                cat2 = categories[i - 1]
                cat1.name, cat2.name = cat2.name, cat1.name
                cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
                cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
                cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
                cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
                cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
        elif m == 'Move_Down':
            i = int(self.Mode.split('-')[1])
            if i + 1 < len(categories):
                cat1 = categories[i]
                cat2 = categories[i + 1]
                cat1.name, cat2.name = cat2.name, cat1.name
                cat1.pn_name, cat2.pn_name = cat2.pn_name, cat1.pn_name
                cat1.pn_show, cat2.pn_show = cat2.pn_show, cat1.pn_show
                cat1.pn_selected, cat2.pn_selected = cat2.pn_selected, cat1.pn_selected
                cat1.Instance_Start, cat2.Instance_Start = cat2.Instance_Start, cat1.Instance_Start
                cat1.Instance_length, cat2.Instance_length = cat2.Instance_length, cat1.Instance_length
        elif self.Mode == 'AddFromFile':
            #Load the File data to FileDisps
            scene = bpy.context.scene
            scene.cr_filecategories.clear()
            scene.cr_filedisp.clear() 
            CR_Prop.FileDisp_Name.clear()
            CR_Prop.FileDisp_Command.clear()
            for folder in os.listdir(path):
                folderpath = path + "/" + folder
                if os.path.isdir(folderpath):
                    textfiles = os.listdir(folderpath)
                    new = scene.cr_filecategories.add()
                    name = "".join(folder.split('~')[1:])
                    new.name = name
                    new.pn_name = name
                    new.pn_show = True
                    new.FileDisp_Start = len(CR_Prop.FileDisp_Name)
                    new.FileDisp_length = len(textfiles)
                    sortedtxt = [None] * len(textfiles)
                    for txt in textfiles:
                        sortedtxt[int(os.path.splitext(txt)[0].split('~')[0])] = txt #remove the .txtending, join to string again, get the index
                    for txt in sortedtxt:
                        blnew = scene.cr_filedisp.add()
                        CR_Prop.FileDisp_Name.append("".join(txt.split('~')[1:]))
                        CmdList = []
                        with open(folderpath + "/" + txt, 'r', encoding='utf8') as text:
                            for line in text.readlines():
                                CmdList.append(line.strip())
                        CR_Prop.FileDisp_Command.append(CmdList)
            bpy.context.area.tag_redraw()
            TempSaveCats()
            return context.window_manager.invoke_props_dialog(self)
        else:
            return context.window_manager.invoke_props_dialog(self)
        bpy.context.area.tag_redraw()
        TempSaveCats()
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        categories = context.scene.cr_categories
        scene = context.scene
        if self.Mode == 'Add':
            layout.prop(self, 'PanelName')
        elif self.Mode == 'Delet':
            for cat in categories:
                layout.prop(cat, 'pn_selected', text= cat.pn_name)
            layout.label(text='')
        elif self.Mode == 'Rename':
            for cat in categories:
                layout.prop(cat, 'pn_selected', text= cat.pn_name)
            layout.prop(self, 'PanelName')
        elif self.Mode == 'Move':
            for cat in categories:
                layout.prop(cat, 'pn_selected', text= cat.pn_name)
        elif self.Mode == 'ToButton':
            for cat in categories:
                layout.prop(cat, 'pn_selected', text= cat.pn_name)
        elif self.Mode == 'AddFromFile':
            for cat in scene.cr_filecategories:
                box = layout.box()
                col = box.column()
                row = col.row()
                if cat.pn_show:
                    row.prop(cat, 'pn_show', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    row.prop(cat, 'pn_show', icon="TRIA_RIGHT", text= "", emboss= False)
                row.label(text= cat.pn_name)
                row.prop(cat, 'pn_selected', text= "")
                if cat.pn_show:
                    col = box.column(align= False)
                    if cat.pn_selected:
                        row2 = col.row()
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.label(text= CR_Prop.FileDisp_Name[i], icon= 'CHECKBOX_HLT')
                    else:
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.prop(scene.cr_filedisp[i], 'Index' , text= CR_Prop.FileDisp_Name[i])
            layout.prop(self, 'NewPanel', text= "Create as a new Panel")

class ImportButton(Operator, ImportHelper):
    bl_idname = "cr.import"
    bl_label = "Import"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )
    files : CollectionProperty(type= PropertyGroup)

    Category : StringProperty(default= "Imports")
    AddNewPanel : BoolProperty(default= False)

    def execute(self, context):
        scene = context.scene
        cr_categories = scene.cr_categories
        if self.filepath.endswith(".zip"):
            with zipfile.ZipFile(self.filepath, 'r') as zip_out:
                filepaths = sorted(zip_out.namelist())
                if self.AddNewPanel:
                    mycat = cr_categories.add()
                    mycat.name = self.Category
                    mycat.pn_name = self.Category
                    mycat.Instance_Start = len(CR_Prop.Instance_Name)
                    for btn_file in filepaths:
                        CR_Prop.Instance_Name.append(os.path.splitext(os.path.basename(btn_file))[0])
                        CR_Prop.Instance_Command.append(zip_out.read(btn_file).decode("utf-8").splitlines())
                        new_e = scene.cr_enum.add()
                        e_index = len(scene.cr_enum) - 1
                        new_e.name = str(e_index)
                        new_e.Index = e_index
                        mycat.Instance_length += 1
                else:
                    dirlist = []
                    tempdirfiles = []
                    dirfileslist = []
                    for btn_file in filepaths:
                        btn_dirc = btn_file.split("/")[0]
                        if btn_dirc not in dirlist:
                            if len(tempdirfiles):
                                dirfileslist.append(tempdirfiles[:])
                            dirlist.append(btn_dirc)
                            tempdirfiles.clear()
                        tempdirfiles.append(btn_file)
                    else:
                        if len(tempdirfiles):
                            dirfileslist.append(tempdirfiles)

                    for i in range(len(dirlist)):
                        Index = None
                        mycat = None
                        for cat in cr_categories:
                            if cat.pn_name == dirlist[i]:
                                Index = GetPanelIndex(cat)
                                break
                        if Index is None:
                            mycat = cr_categories.add()
                            name = dirlist[i]
                            mycat.name = name
                            mycat.pn_name = name
                            mycat.Instance_Start = len(CR_Prop.Instance_Name)
                        else:
                            mycat = cr_categories[Index]
                        for dir_file in dirfileslist[i]:
                            inserti = mycat.Instance_Start + mycat.Instance_length
                            CR_Prop.Instance_Name.insert(inserti, os.path.splitext(os.path.basename(dir_file))[0])
                            CR_Prop.Instance_Command.insert(inserti, zip_out.read(dir_file).decode("utf-8").splitlines())
                            new_e = scene.cr_enum.add()
                            e_index = len(scene.cr_enum) - 1
                            new_e.name = str(e_index)
                            new_e.Index = e_index
                            mycat.Instance_length += 1
                            if Index is not None:
                                for cat in cr_categories[Index + 1:] :
                                    cat.Instance_Start += 1
            SetEnumIndex()
        else:
            self.report({'ERROR'}, "{ " + path + " } Select a .zip file")
        return {"FINISHED"}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'AddNewPanel', text= "Create new Panel")
        if self.AddNewPanel:
            layout.prop(self, 'Category', text= "Category")

class ExportButton(Operator, ExportHelper):
    bl_idname = "cr.export"
    bl_label = "Export"

    filter_glob: StringProperty( default='*.zip', options={'HIDDEN'} )
    filename_ext = ".zip"
    filepath : StringProperty (name = "File Path", maxlen = 1024, default = "ComandRecorderButtons")

    def execute(self, context):
        scene = context.scene
        temppath = bpy.app.tempdir + "CR_Zip"
        if not os.path.exists(temppath):
            os.mkdir(temppath)
        with zipfile.ZipFile(self.filepath, 'w') as zip_it:
            for cat in scene.cr_filecategories:
                folderpath = temppath + "/" + cat.pn_name
                if not os.path.exists(folderpath):
                    os.mkdir(folderpath)
                if cat.pn_selected:
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        path = folderpath + "/" + CR_Prop.FileDisp_Name[i] + ".txt"
                        with open(path, 'w', encoding='utf8') as recfile:
                            for cmd in CR_Prop.FileDisp_Command[i]:
                                recfile.write(cmd + '\n')
                        zip_it.write(path, cat.pn_name + "/" + CR_Prop.FileDisp_Name[i] + ".txt")
                        os.remove(path)
                else:
                    for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                        if scene.cr_filedisp[i].Index:
                            path = folderpath + "/" + CR_Prop.FileDisp_Name[i] + ".txt"
                            with open(path, 'w', encoding='utf8') as recfile:
                                for cmd in CR_Prop.FileDisp_Command[i]:
                                    recfile.write(cmd + '\n')
                            zip_it.write(path, cat.pn_name + "/" + CR_Prop.FileDisp_Name[i] + ".txt")
                            os.remove(path)
                os.rmdir(folderpath)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        for cat in scene.cr_filecategories:
                box = layout.box()
                col = box.column()
                row = col.row()
                if cat.pn_show:
                    row.prop(cat, 'pn_show', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    row.prop(cat, 'pn_show', icon="TRIA_RIGHT", text= "", emboss= False)
                row.label(text= cat.pn_name)
                row.prop(cat, 'pn_selected', text= "")
                if cat.pn_show:
                    col = box.column(align= False)
                    if cat.pn_selected:
                        row2 = col.row()
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.label(text= CR_Prop.FileDisp_Name[i], icon= 'CHECKBOX_HLT')
                    else:
                        for i in range(cat.FileDisp_Start, cat.FileDisp_Start + cat.FileDisp_length):
                            col.prop(scene.cr_filedisp[i], 'Index' , text= CR_Prop.FileDisp_Name[i])
    
    def invoke(self, context, event):
        scene = context.scene
        scene.cr_filecategories.clear()
        for cat in scene.cr_categories:
            new = scene.cr_filecategories.add()
            new.name = cat.name
            new.pn_name = cat.pn_name
            new.FileDisp_Start = cat.Instance_Start
            new.FileDisp_length = cat.Instance_length
        CR_Prop.FileDisp_Name = CR_Prop.Instance_Name[:]
        CR_Prop.FileDisp_Command = CR_Prop.Instance_Command[:]
        scene.cr_filedisp.clear()
        for i in range(len(scene.cr_enum)):
            scene.cr_filedisp.add()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class CR_PT_Panel_VIEW_3D(CR_PT_Panel):
    bl_space_type = 'VIEW_3D'# メニューを表示するエリア
    bl_idname = 'command_panel_view_3d'
class CR_PT_Panel_IMAGE_EDITOR(CR_PT_Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_idname = 'command_panel_image_editor'

Icurrentselected = [None]
Ilastselected = [None]
def Instance_Updater(self, context):
    enum = context.scene.cr_enum
    for e in enum:
        if not e.Value and Ilastselected[0] == e.Index and Icurrentselected[0] == e.Index:
            e.Value = True
        elif e.Value and Ilastselected[0] != e.Index and Icurrentselected[0] != e.Index:
            Icurrentselected[0] = e.Index
            if Ilastselected[0] is not None:
                try:
                    enum[Ilastselected[0]].Value = False
                except:
                    Ilastselected[0] = None 
            Ilastselected[0] = e.Index
            context.scene.CR_Var.Instance_Index = e.Index

class CR_Enum(PropertyGroup):
    Value : BoolProperty(default= False, update= Instance_Updater)
    Index : IntProperty()
    Init = True

class CR_FileDisp(PropertyGroup):
    Index : BoolProperty(default= False)

class CategorizeFileDisp(PropertyGroup):
    pn_name : StringProperty()
    pn_show : BoolProperty(default= True)
    pn_selected : BoolProperty(default= False)
    FileDisp_Start : IntProperty(default= 0)
    FileDisp_length : IntProperty(default= 0)

class CR_Prop(PropertyGroup):#何かとプロパティを収納
    Rename : StringProperty() #CR_Var.name

    Instance_Name = []
    Instance_Command = []
    Instance_Index : IntProperty(default= 0)

    FileDisp_Name = []
    FileDisp_Command = []
    FileDisp_Index : IntProperty(default= 0)

    IgnoreUndo : BoolProperty(default=True, description="all records and changes are unaffected by undo")
    PanelType : EnumProperty(items= [("button","Button",""),("record","Record","")], default= "record")
    ShowMenu : BoolProperty(description= "shows an extra menu with import/export options")
    ShowMacros : BoolProperty(description= "shows an extra menu with the macros", default= True)

    Temp_Command = []
    Temp_Num = 0
    for Num_Loop in range(256) :
        exec('List_Index_{0:03d} : IntProperty(default = 0)'.format(Num_Loop))
        exec('List_Command_{0:03d} : CollectionProperty(type = CR_OT_String)'.format(Num_Loop))

    #==============================================================
    # (キーが押されたときに実行する bpy.types.Operator のbl_idname, キー, イベント, Ctrlキー, Altキー, Shiftキー)
    addon_keymaps = []
    key_assign_list = \
    [
    (Command_OT_Add.bl_idname, 'COMMA', 'PRESS', False, False, True),
    (Command_OT_Play.bl_idname, 'PERIOD', 'PRESS', False, False, True),
    (CR_OT_Selector_Up.bl_idname, 'WHEELUPMOUSE','PRESS', False, False, True),
    (CR_OT_Selector_Down.bl_idname, 'WHEELDOWNMOUSE','PRESS', False, False, True)
    ]



#==============================================================
#プロパティの宣言
#-------------------------------------------------------------------------------------------
def Initialize_Props():# プロパティをセットする関数
    bpy.types.Scene.cr_categories = CollectionProperty(type= CategorizeProps)
    bpy.types.Scene.CR_Var = PointerProperty(type=CR_Prop)
    bpy.types.Scene.cr_enum = CollectionProperty(type= CR_Enum)
    bpy.types.Scene.cr_filecategories = CollectionProperty(type= CategorizeFileDisp)
    bpy.types.Scene.cr_filedisp = CollectionProperty(type= CR_FileDisp)
    bpy.app.handlers.load_factory_preferences_post.append(InitSavedPanel)
    bpy.app.handlers.load_post.append(InitSavedPanel)
    bpy.app.handlers.undo_pre.append(SaveUndoStep)
    bpy.app.handlers.redo_post.append(GetRedoStep)
    bpy.app.handlers.undo_post.append(TempLoad) # add TempLoad to ActionHandler and call ist after undo
    bpy.app.handlers.redo_post.append(TempLoad) # also for redo
    bpy.app.handlers.undo_post.append(TempLoadCats)
    bpy.app.handlers.redo_post.append(TempLoadCats)
    bpy.app.handlers.undo_pre.append(InitTemp)
    if bpy.context.window_manager.keyconfigs.addon:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')#Nullとして登録
        CR_Prop.addon_keymaps.append(km)
        for (idname, key, event, ctrl, alt, shift) in CR_Prop.key_assign_list:
            kmi = km.keymap_items.new(idname, key, event, ctrl=ctrl, alt=alt, shift=shift)# ショートカットキーの登録

def Clear_Props():
    del bpy.types.Scene.cr_categories
    del bpy.types.Scene.CR_Var
    del bpy.types.Scene.cr_enum
    del bpy.types.Scene.cr_filedisp
    del bpy.types.Scene.cr_filecategories
    bpy.app.handlers.load_factory_preferences_post.remove(InitSavedPanel)
    bpy.app.handlers.load_post.remove(InitSavedPanel)
    bpy.app.handlers.undo_pre.remove(SaveUndoStep)
    bpy.app.handlers.redo_post.remove(GetRedoStep)
    bpy.app.handlers.undo_post.remove(TempLoad)
    bpy.app.handlers.redo_post.remove(TempLoad)
    bpy.app.handlers.undo_post.remove(TempLoadCats)
    bpy.app.handlers.redo_post.remove(TempLoadCats)
    bpy.app.handlers.undo_pre.remove(InitTemp)
    for km in CR_Prop.addon_keymaps:
        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)
    CR_Prop.addon_keymaps.clear()



#==============================================================
#Blenderへ登録
#-------------------------------------------------------------------------------------------
#使用されているクラスを格納
Class_List = \
[
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
CR_PT_Panel_VIEW_3D,
CR_PT_Panel_IMAGE_EDITOR,
CategorizeProps,
AddCategory,
CR_Enum,
CategorizeFileDisp,
CR_FileDisp,
ImportButton,
ExportButton
]

