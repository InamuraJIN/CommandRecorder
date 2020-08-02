# ==============================================================
# スタートアップ
# -------------------------------------------------------------------------------------------
import bpy  # Blender内部のデータ構造にアクセスするために必要

from .blender_module_utils import get_bpy_classes, forEach
from . import operators
from . import panels

# ==============================================================
# プラグインに関する情報
# ==============================================================
bl_info = {
    "name": "CommandRecorder",  # プラグイン名
    "author": "BuuGraphic",  # 作者
    "version": (2, 0, 3),  # プラグインのバージョン
    "blender": (2, 80, 0),  # プラグインが動作するBlenderのバージョン
    "location": "View 3D",  # Blender内部でのプラグインの位置づけ
    "description": "Thank you for using our services",  # プラグインの説明
    "warning": "",
    "wiki_url": "https://twitter.com/Sample_Mu03",  # プラグインの説明が存在するWikiページのURL
    "tracker_url": "https://twitter.com/Sample_Mu03",  # Blender Developer OrgのスレッドURL
    "link": "https://twitter.com/Sample_Mu03",
    "category": "System",  # プラグインのカテゴリ名
}

# ==============================================================
# blenderへ登録
# ==============================================================
def register():
    forEach(get_bpy_classes(operators), bpy.utils.register_class)
    # パネルは登録順が重要
    forEach(panels.classes, bpy.utils.register_class)
    print("Register")


def unregister():
    forEach(get_bpy_classes(operators), bpy.utils.unregister_class)
    forEach(get_bpy_classes(panels), bpy.utils.unregister_class)

    print("UnRegister")


if __name__ == "__main__":
    register()