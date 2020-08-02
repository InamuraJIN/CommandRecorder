import os
from unittest import TestLoader, TextTestRunner
from unittest import runner

"""
blender -b -P discover_tests.py
"""
print(f'{__file__} __package__:' + str(__package__))

if __name__ == "__main__":
    loader = TestLoader()
    test = loader.discover(os.getcwd(), top_level_dir=os.path.dirname(os.getcwd()))
    runner = TextTestRunner()
    runner.run(test)
