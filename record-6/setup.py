from setuptools import setup
from Cython.Build import cythonize
import os

def find_all_py_files(folder):
    py_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                py_files.append(os.path.join(root, file))
    return py_files

# all_py_files = ["ring_server_serial.py", "config.py"] + find_all_py_files("core")
all_py_files = ["ring_server_serial.py", "config.py", "core/ring/utils/imu_data.py", "core/ring/qt/ble_ring_v2_serial.py", "core/utils/window.py"]

setup(
    ext_modules=cythonize(all_py_files, compiler_directives={"language_level": "3"}),
)