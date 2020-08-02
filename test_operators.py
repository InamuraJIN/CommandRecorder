import bpy
import sys, os
import unittest

"""
blender -b -P test_operators.py
"""

# fake as a module.
__package__ = os.path.basename(os.path.dirname(__file__))


class Test(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
