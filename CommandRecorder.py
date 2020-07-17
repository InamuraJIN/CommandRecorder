#==============================================================
#スタートアップ
#-------------------------------------------------------------------------------------------
import bpy #Blender内部のデータ構造にアクセスするために必要
from bpy.app.handlers import persistent
import os
import shutil
import json
from json.decoder import JSONDecodeError

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


#==============================================================
#使用クラスの宣言
#-------------------------------------------------------------------------------------------
class CR_OT_String(PropertyGroup):#リストデータを保持するためのプロパティグループを作成
    Command : StringProperty(
    default=''
    ) #CR_Var.name

class CR_List_Selector(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.name)
class CR_List_Command(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.name)
class CR_List_Instance(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        layout.label(text = item.name)


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
        CR_PT_List.Bool_Record = 1
        CR_Prop.Temp_Num = len(Recent)
    else:
        CR_PT_List.Bool_Record = 0
        for i in range (CR_Prop.Temp_Num, len(Recent)):
            TempText = Recent[i-1].body
            if TempText.count('bpy'):
                Item = CR_('List', Num).add()
                Item.name = TempText[TempText.find('bpy'):]

tpath = bpy.app.tempdir + "temp.json"

def CreateTempFile():
    if not os.path.exists(tpath):
        print(tpath)
        with open(tpath, 'w', encoding='utf8') as tempfile:
            json.dump({"0":[]}, tempfile)

def TempSave(Num):  # write new command to temp.json file
    CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:   
        data = json.load(tempfile)
        data.update({str(Num):[]})
        data["0"].append(CR_('List', 0)[Num - 1]['name'])
        tempfile.seek(0)
        json.dump(data, tempfile)

def TempUpdate(): # update all commands in temp.json file
    CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        tempfile.truncate(0)
        tempfile.seek(0)
        data = {}
        for cmd in range(len(CR_('List', 0)) + 1):
            data.update({str(cmd):[i.name for i in CR_('List', cmd)]})
        json.dump(data, tempfile)

def TempUpdateCommand(Key): # update one command in temp.json file
    CreateTempFile()
    with open(tpath, 'r+', encoding='utf8') as tempfile:
        data = json.load(tempfile)
        data[str(Key)] = [i.name for i in CR_('List', int(Key))]
        tempfile.truncate(0)
        tempfile.seek(0)
        json.dump(data, tempfile)

@persistent
def TempLoad(dummy): # load commands after undo
    if bpy.context.scene.CR_Var.IgnoreUndo:
        with open(tpath, 'r', encoding='utf8') as tempfile:
            data = json.load(tempfile)
        command = CR_('List', 0)
        command.clear()
        keys = list(data.keys())
        for i in range(1, len(data)):
            Item = command.add()
            Item.name = data["0"][i - 1]
            record = CR_('List', i)
            record.clear()
            for j in range(len(data[keys[i]])):
                Item = record.add()
                Item.name = data[keys[i]][j]

UndoRedoStack = []

def GetCommand(scene, index):
    return eval('scene.CR_Var.List_Command_{0:03d}'.format(index))

@persistent
def SaveUndoStep(scene):
    All = []
    l = []
    l.append([i.name for i in list(GetCommand(scene, 0))])
    for x in range(1, len(l[0]) + 1):
        l.append([ i.name for i in list(GetCommand(scene, x))])
    UndoRedoStack.append(l)

@persistent
def GetRedoStep(dummy):
    command = CR_('List', 0)
    command.clear()
    l = UndoRedoStack[len(UndoRedoStack) - 1]
    for i in range(1, len(l[0]) + 1):
        item = command.add()
        item.name = l[0][i - 1]
        record = CR_('List', i)
        record.clear()
        for j in range(len(l[i])):
            item = record.add()
            item.name = l[i][j]
    UndoRedoStack.pop()


def Add(Num):
    Recent = Get_Recent('Reports_All')
    if Num or len(CR_('List', 0)) < 250:
        Item = CR_('List', Num).add()
        if Num:
            if Recent[-2].body.count('bpy'):
                Name_Temp = Recent[-2].body
                Item.name = Name_Temp[Name_Temp.find('bpy'):]
            else:
                Name_Temp = Recent[-3].body
                Item.name = Name_Temp[Name_Temp.find('bpy'):]
        else:
            Item.name = 'Untitled_{0:03d}'.format(len(CR_('List', Num)))
        CR_( len(CR_('List',Num))-1, Num )

def Remove(Num):
    if not Num:
        for Num_Loop in range(CR_('Index',0)+1 , len(CR_('List',0))+1) :
            CR_('List',Num_Loop).clear()
            for Num_Command in range(len(CR_('List',Num_Loop+1))) :
                Item = CR_('List',Num_Loop).add()
                Item.name = CR_('List',Num_Loop+1)[Num_Command].name
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
                Item.name = Num_Command.name
            CR_(CR_('Index',index2),254)
            CR_('List',index2).clear()
            #Index1からIndex2へ
            for Num_Command in CR_('List',index1) :
                Item = CR_('List',index2).add()
                Item.name = Num_Command.name
            CR_(CR_('Index',index1),index2)
            CR_('List',index1).clear()
            #254からIndex1へ
            for Num_Command in CR_('List',254) :
                Item = CR_('List',index1).add()
                Item.name = Num_Command.name
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
    if scene.CR_Var.Target_Switch == 'Once': #Target Switch is always 'Once'
        for Command in Commands :
            if type(Command) == str :
                exec(Command)
            else :
                exec(Command.name)
    else :      
        current_mode = bpy.context.mode
        Set_DeSelect = ''
        Set_Select = []
        Set_Active = []
        if current_mode == 'OBJECT':
            Set_DeSelect = ("bpy.ops.object.select_all(action='DESELECT')")
            for Target in bpy.context.selected_objects:
                Set_Select.append("bpy.data.objects['{0}'].select = True".format(Target.name))
                Set_Active.append("bpy.context.scene.objects.active = bpy.data.objects['{0}']".format(Target.name))
        elif current_mode == 'EDIT_MESH':
            pass

        elif current_mode == 'EDIT_ARMATURE':
            Arm = bpy.context.scene.objects.active.name
            Set_DeSelect = ("bpy.ops.armature.select_all(action='DESELECT')")
            for Target in bpy.context.selected_editable_bones :
                Set_Select.append("bpy.data.objects['{0}'].data.edit_bones['{1}'].select = True".format(Arm , Target.name))
                Set_Active.append("bpy.data.objects['{0}'].data.edit_bones.active = bpy.data.objects['{0}'].data.edit_bones['{1}']".format(Arm , Target.name))

        elif current_mode == 'POSE':
            Arm = bpy.context.scene.objects.active.name
            Set_DeSelect = ("bpy.ops.pose.select_all(action='DESELECT')")
            for Target in bpy.context.selected_pose_bones :
                print('a')
                Set_Select.append("bpy.data.objects['{0}'].pose.bones['{1}'].bone.select = True".format(Arm , Target.name))
                Set_Active.append("bpy.data.objects['{0}'].data.bones.active = bpy.data.objects['{0}'].data.bones['{1}']".format(Arm , Target.name))

        for Num_Loop in range(len(Set_Select)) :
            print(Set_DeSelect)
            print(Set_Select[Num_Loop])
            print(Set_Active[Num_Loop])
            exec(Set_DeSelect)
            exec(Set_Select[Num_Loop])
            exec(Set_Active[Num_Loop])
            if current_mode == 'EDIT_ARMATURE' :
                bpy.ops.object.mode_set(mode='POSE')
                bpy.ops.object.mode_set(mode='EDIT')
            for Command in Commands :
                if type(Command) == str :
                    exec(Command)
                else :
                    exec(Command.name)

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
        panelpath = path + "/" + cat.pn_name + f"–{GetPanelIndex(cat)}"
        os.mkdir(panelpath)
        for cmd_i in range(cat.Instance_Start, cat.Instance_Start + cat.Instance_length):
            with open(panelpath + "/" + CR_Prop.Instance_Name[cmd_i] + f"–{cmd_i}", 'w') as cmd_file:
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
            name = folder.split('–')[0]
            new.name = name
            new.pn_name = name
            new.pn_show = True
            new.Instance_Start = len(CR_Prop.Instance_Name)
            new.Instance_length = len(textfiles)
            sortedtxt = [None] * len(textfiles)
            for txt in textfiles:
                sortedtxt[int(''.join(txt.split('.')[:-1]).split('–')[1])] = txt #remove the .txtending, join to string again, get the index

            for txt in sortedtxt:
                blnew = scene.cr_enum.add()
                CR_Prop.Instance_Name.append(txt.split('–')[0])
                CmdList = []
                with open(folderpath + "/" + txt, 'r') as text:
                    for line in text.readlines():
                        CmdList.append(line.strip())
                CR_Prop.Instance_Command.append(CmdList)
    if len(scene.cr_enum) != 0:
        scene.cr_enum[0].Index = True

def Recorder_to_Instance(panel):
    i = panel.Instance_Start +  panel.Instance_length
    CR_Prop.Instance_Name.insert(i, CR_('List',0)[CR_('Index',0)].name)
    Temp_Command = []
    for Command in CR_('List',CR_('Index',0)+1):
        Temp_Command.append(Command.name)
    CR_Prop.Instance_Command.insert(i, Temp_Command)
    panel.Instance_length += 1
    bpy.context.scene.cr_enum.add()
    p_i = GetPanelIndex(panel)
    categories = bpy.context.scene.cr_categories
    if p_i < len(categories):
        for cat in categories[ p_i + 1: ]:
            cat.Instance_Start += 1

def Instance_to_Recorder():
    scene = bpy.context.scene
    Item = CR_('List' , 0 ).add()
    Item.name = CR_Prop.Instance_Name[scene.CR_Var.Instance_Index]
    for Command in CR_Prop.Instance_Command[scene.CR_Var.Instance_Index] :
        Item = CR_('List' , len(CR_('List',0)) ).add()
        Item.name = Command
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
        scene.cr_enum.remove(Index)
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
        scene.cr_enum[index2].Index = True

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
        #コマンドをインスタンスに
        elif self.Mode == 'Instance_to_Recorder' :
            Instance_to_Recorder()
        #削除
        elif self.Mode == 'I_Remove' :
            I_Remove()
        #上へ
        elif self.Mode == 'I_Up' :
            I_Move('Up')
        #下へ
        elif self.Mode == 'I_Down' :
            I_Move('Down')
        #インスタンスのリネーム
        elif self.Mode == 'Rename' :
            Rename_Instance()
        #インスタンスを実行
        else :
            Execute_Instance(CR_Prop.Instance_Name.index(self.Mode))

        bpy.context.area.tag_redraw()
        return{'FINISHED'}#UI系の関数の最後には必ず付ける

def Recent_Switch(Mode):
    if Mode == 'Standard' :
        bpy.app.debug_wm = 0
    else :
        bpy.app.debug_wm = 1
    CR_PT_List.Bool_Recent = Mode


#==============================================================
#レイアウト
#-------------------------------------------------------------------------------------------
# メニュー
class CR_PT_List(bpy.types.Panel):
    bl_region_type = 'UI'# メニューを表示するリージョン
    bl_category = 'CommandRecorder'# メニュータブのヘッダー名
    bl_label = 'CommandRecorder'# タイトル
    #変数の宣言
    #-------------------------------------------------------------------------------------------
    Bool_Record = 0
    Bool_Recent = ''

    #レイアウト
    #-------------------------------------------------------------------------------------------
    def draw_header(self, context):
        self.layout.label(text = '', icon = 'REC')
    #メニューの描画処理
    def draw(self, context):
        scene = bpy.context.scene
        #-------------------------------------------------------------------------------------------
        layout = self.layout
        box = layout.box()
        box_row = box.row()
        box_row.label(text = '', icon = 'SETTINGS')
        if len(CR_('List',0)) :
            box_row.prop(CR_('List',0)[CR_('Index',0)] , 'name' , text='')
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
            box_row = box.row()
            box_row.label(text = '', icon = 'TEXT')
            if len(CR_('List',CR_('Index',0)+1)) :
                box_row.prop(CR_('List',CR_('Index',0)+1)[CR_('Index',CR_('Index',0)+1)],'name' , text='')
            box_row = box.row()
            col = box_row.column()
            col.template_list('CR_List_Command' , '' , scene.CR_Var , 'List_Command_{0:03d}'.format(CR_('Index',0)+1) , scene.CR_Var , 'List_Index_{0:03d}'.format(CR_('Index',0)+1), rows=4)
            col = box_row.column()
            if CR_PT_List.Bool_Record :
                col.operator(CR_OT_Command.bl_idname , text='' , icon='PAUSE' ).Mode = 'Record_Stop'
            else :
                col.operator(CR_OT_Command.bl_idname , text='' , icon='REC' ).Mode = 'Record_Start'
                col.operator(Command_OT_Add.bl_idname , text='' , icon='ADD' )
                col.operator(CR_OT_Command.bl_idname , text='' , icon='REMOVE' ).Mode = 'Remove'
                col.operator(CR_OT_Command.bl_idname , text='' , icon='TRIA_UP' ).Mode = 'Up'
                col.operator(CR_OT_Command.bl_idname , text='' , icon='TRIA_DOWN' ).Mode = 'Down'
            if len(CR_('List',CR_('Index',0)+1)) :
                box.operator(Command_OT_Play.bl_idname , text='Play' )
                box.operator(AddCategory.bl_idname , text='Recorder to Button' ).Mode = 'ToButton'
                box.operator(CR_OT_Command.bl_idname , text='Clear').Mode = 'Clear'
        box = layout.box()
        box.label(text = 'Options', icon = 'PRESET_NEW')
        #box_row = box.row()
        #box_row.label(text = 'Target')
        #box_row.prop(scene.CR_Var, 'Target_Switch' ,expand = 1)
        box_row = box.row()
        box_row.label(text = 'History')
        box_row.prop(scene.CR_Var, 'Recent_Switch' ,expand = 1)
        if not(CR_PT_List.Bool_Recent == scene.CR_Var.Recent_Switch) :
            Recent_Switch(scene.CR_Var.Recent_Switch)
        box_row = box.row()
        box_row.label(text = 'Ignore Undo')
        box_row.prop(scene.CR_Var, 'IgnoreUndo', toggle = 1, text="Ignore")
        
class CR_PT_Instance(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'# メニューを表示するエリア
    bl_region_type = 'UI'# メニューを表示するリージョン
    bl_category = 'CommandRecorder'# メニュータブのヘッダー名
    bl_label = 'CommandButton'# タイトル
    #変数の宣言
    #-------------------------------------------------------------------------------------------
    SelectedInctance = ''
    #レイアウト
    #-------------------------------------------------------------------------------------------
    def draw_header(self, context):
        self.layout.label(text = '', icon = 'PREFERENCES')
    #メニューの描画処理
    def draw(self, context):
        scene = bpy.context.scene
        #-------------------------------------------------------------------------------------------
        layout = self.layout
        #
        box = layout.box()
        box.operator(CR_OT_Instance.bl_idname , text='Button to Recorder' ).Mode = 'Instance_to_Recorder'
        box.operator(CR_OT_Instance.bl_idname , text='Save to File' ).Mode = 'Save'
        box.operator(CR_OT_Instance.bl_idname , text='Load from File' ).Mode = 'Load'
        if len(CR_Prop.Instance_Name) :
            box_row = box.row()
            row2 = box_row.row(align= True)
            row2.operator(CR_OT_Instance.bl_idname , text='' , icon='REMOVE' ).Mode = 'I_Remove'
            row2.operator(CR_OT_Instance.bl_idname , text='' , icon='TRIA_UP' ).Mode = 'I_Up'
            row2.operator(CR_OT_Instance.bl_idname , text='' , icon='TRIA_DOWN' ).Mode = 'I_Down'
            box_row.prop(scene.CR_Var , 'Rename' , text='')
            box_row.operator(CR_OT_Instance.bl_idname , text='Rename').Mode = 'Rename'
        row = box.row()
        col = row.column()
        col.label(text= 'Category')
        col = row.column()
        row2 = col.row(align= True)
        row2.scale_x = 1.15
        row2.operator(AddCategory.bl_idname, text= '', icon= 'ADD').Mode = 'Add'
        row2.operator(AddCategory.bl_idname, text= '', icon= 'TRASH').Mode = 'Delet'
        row2.operator(AddCategory.bl_idname, text= '', icon= 'GREASEPENCIL').Mode = 'Rename'
        row2.operator(AddCategory.bl_idname, text= '', icon= 'PRESET').Mode = 'Move'
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
                    col.prop(scene.cr_enum[i], 'Index' ,toggle = 1, text= str(i + 1))
                col = split.column()
                col.scale_y = 0.9493
                for Num_Loop in range(cat.Instance_Start, cat.Instance_Start + cat.Instance_length):
                    col.operator(CR_OT_Instance.bl_idname , text=CR_Prop.Instance_Name[Num_Loop]).Mode = CR_Prop.Instance_Name[Num_Loop]

currentselected = [None]
lastselected = [None]
def UseRadioButtons(self, context):
    categories = context.scene.cr_categories
    for cat in categories:
        if cat.pn_selected and lastselected[0] != cat and currentselected[0] != cat:
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

class AddCategory(bpy.types.Operator):
    bl_idname = "cr.add_category"
    bl_label = "Category"

    Mode : StringProperty()
    PanelName : StringProperty(name = "Panel Name", default="")

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
                    categories.remove(GetPanelIndex(cat))
        elif self.Mode == 'Rename':
            for cat in categories:
                if cat.pn_selected:
                    cat.name = self.PanelName
                    cat.pn_name = self.PanelName
        elif self.Mode == 'Move':
            for cat in categories:
                if cat.pn_selected:
                    Index = scene.CR_Var.Instance_Index
                    catendl = cat.Instance_Start + cat.Instance_length - 1
                    for curcat in categories:
                        if Index >= curcat.Instance_Start and Index < curcat.Instance_Start + curcat.Instance_length:
                            curcat.Instance_length -= 1
                            break
                    CR_Prop.Instance_Name.insert(catendl, CR_Prop.Instance_Name.pop(Index))
                    CR_Prop.Instance_Command.insert(catendl, CR_Prop.Instance_Command.pop(Index))
                    cat.Instance_length += 1
                    cat.Instance_Start -= 1
                    scene.cr_enum[catendl].Index = True
        elif self.Mode == 'ToButton':
            for cat in categories:
                if cat.pn_selected:
                    Recorder_to_Instance(cat)
        return {"FINISHED"}

    def invoke(self, context, event):
        m = self.Mode.split('-')[0]
        categories = context.scene.cr_categories
        if m == 'Move_Up':
            i = int(self.Mode.split('-')[1])
            if i - 1 >= 0:
                categories[i].name, categories[i - 1].name = categories[i - 1].name, categories[i].name
                categories[i].pn_name, categories[i - 1].pn_name = categories[i - 1].pn_name, categories[i].pn_name
                categories[i].pn_show, categories[i - 1].pn_show = categories[i - 1].pn_show, categories[i].pn_show
                categories[i].pn_selected, categories[i - 1].pn_selected = categories[i - 1].pn_selected, categories[i].pn_selected
                categories[i].Instance_Start, categories[i - 1].Instance_Start = categories[i - 1].Instance_Start, categories[i].Instance_Start
                categories[i].Instance_length, categories[i - 1].Instance_length = categories[i - 1].Instance_length, categories[i].Instance_length
        elif m == 'Move_Down':
            i = int(self.Mode.split('-')[1])
            if i + 1 < len(categories):
                categories[i].name, categories[i - 1].name = categories[i - 1].name, categories[i].name
                categories[i].pn_name, categories[i - 1].pn_name = categories[i - 1].pn_name, categories[i].pn_name
                categories[i].pn_show, categories[i - 1].pn_show = categories[i - 1].pn_show, categories[i].pn_show
                categories[i].pn_selected, categories[i - 1].pn_selected = categories[i - 1].pn_selected, categories[i].pn_selected
                categories[i].Instance_Start, categories[i - 1].Instance_Start = categories[i - 1].Instance_Start, categories[i].Instance_Start
                categories[i].Instance_length, categories[i - 1].Instance_length = categories[i - 1].Instance_length, categories[i].Instance_length
        else:
            return context.window_manager.invoke_props_dialog(self)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        categories = context.scene.cr_categories
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

class CR_List_PT_VIEW_3D(CR_PT_List):
    bl_space_type = 'VIEW_3D'# メニューを表示するエリア
class CR_PT_Instance_VIEW_3D(CR_PT_Instance):
    bl_space_type = 'VIEW_3D'# メニューを表示するエリア
    bl_idname = 'command_list_view_3d'
class CR_List_PT_IMAGE_EDITOR(CR_PT_List):
    bl_space_type = 'IMAGE_EDITOR'
class CR_PT_Instance_IMAGE_EDITOR(CR_PT_Instance):
    bl_space_type = 'IMAGE_EDITOR'
    bl_idname = 'command_list_image_editor'

Icurrentselected = [None]
Ilastselected = [None]
def Instance_Updater(self, context):
    enum = context.scene.cr_enum
    for e in enum:
        if e.Index and Ilastselected[0] != e and Icurrentselected[0] != e:
            Icurrentselected[0] = e
            if Ilastselected[0] is not None:
                Ilastselected[0].Index = False
            Ilastselected[0] = e
            context.scene.CR_Var.Instance_Index = GetPanelIndex(e)

class CR_Enum(PropertyGroup):
    Index : BoolProperty(default= False, update= Instance_Updater)

class CR_Prop(PropertyGroup):#何かとプロパティを収納
    Rename : StringProperty(
    ) #CR_Var.name

    Instance_Name = []
    Instance_Command = []

    Instance_Index : IntProperty(default= 0)
    #コマンド切り替え
    Target_Switch : EnumProperty(
    items = [
    ('Once' , 'Once' , ''),
    ('Each' , 'Each' , ''),
    ])
    #履歴の詳細
    Recent_Switch : EnumProperty(
    items = [
    ('Standard' , 'Standard' , ''),
    ('Extend' , 'Extend' , ''),
    ])

    IgnoreUndo : BoolProperty(default=True, description="all records and changes are unaffected by undo")

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
    bpy.types.Scene.CR_Var = bpy.props.PointerProperty(type=CR_Prop)
    bpy.types.Scene.cr_enum = CollectionProperty(type= CR_Enum)
    bpy.app.handlers.load_factory_preferences_post.append(InitSavedPanel)
    bpy.app.handlers.load_post.append(InitSavedPanel)
    bpy.app.handlers.undo_pre.append(SaveUndoStep)
    bpy.app.handlers.redo_post.append(GetRedoStep)
    bpy.app.handlers.undo_post.append(TempLoad) # add TempLoad to ActionHandler and call ist after undo
    bpy.app.handlers.redo_post.append(TempLoad) # also for redo
    if bpy.context.window_manager.keyconfigs.addon:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')#Nullとして登録
        CR_Prop.addon_keymaps.append(km)
        for (idname, key, event, ctrl, alt, shift) in CR_Prop.key_assign_list:
            kmi = km.keymap_items.new(idname, key, event, ctrl=ctrl, alt=alt, shift=shift)# ショートカットキーの登録

def Clear_Props():
    del bpy.types.Scene.cr_categories
    del bpy.types.Scene.CR_Var
    del bpy.types.Scene.cr_enum
    bpy.app.handlers.load_factory_preferences_post.remove(InitSavedPanel)
    bpy.app.handlers.load_post.remove(InitSavedPanel)
    bpy.app.handlers.undo_pre.remove(SaveUndoStep)
    bpy.app.handlers.redo_post.remove(GetRedoStep)
    bpy.app.handlers.undo_post.remove(TempLoad)
    bpy.app.handlers.redo_post.remove(TempLoad)
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
CR_List_PT_VIEW_3D,
CR_PT_Instance_VIEW_3D,
CR_List_PT_IMAGE_EDITOR,
CR_PT_Instance_IMAGE_EDITOR,
CategorizeProps,
AddCategory,
CR_Enum
]