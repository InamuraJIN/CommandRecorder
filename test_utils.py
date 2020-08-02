from .utils.macro import (
    get_or_create_local_macro,
    list_global_macro_names,
    list_local_macro_names,
    read_from_global_macro,
    read_from_local_macro,
    write_to_global_macro,
    add_to_local_macro,
)
import sys, os
import unittest

"""
blender -b -P test_operators.py
"""

# fake as a module.
__package__ = os.path.basename(os.path.dirname(__file__))


sample_text = """
bpy.ops.transform.translate(value=(1.88828, 1.26826, -2.43953), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
bpy.ops.transform.translate(value=(-2.93417, -3.38876, 2.64027), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
bpy.ops.transform.translate(value=(1.84449, 1.78805, -1.93739), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
"""


class Test(unittest.TestCase):
    def test_text_data(self):
        add_to_local_macro("test", sample_text)
        text = read_from_local_macro("test")

        self.assertEqual(sample_text + "\n", text)

    def test_storage(self):
        write_to_global_macro("test", sample_text)
        text = read_from_global_macro("test")

        self.assertEqual(sample_text, text)

    def test_list_local_macro_names(self):
        get_or_create_local_macro("1")
        get_or_create_local_macro("2")
        get_or_create_local_macro("3")
        get_or_create_local_macro("4")
        local_macro_names = list_local_macro_names()
        print("local_macro_names:" + str(local_macro_names))

    def test_list_grobal_macro_names(self):
        global_macro_names = list_global_macro_names()
        print("global_macro_names:" + str(global_macro_names))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
