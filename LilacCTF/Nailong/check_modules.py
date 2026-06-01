
import torch
import sys
import os

print("Torch version:", torch.__version__)

def find_os_exporters():
    safe_looking_modules = [
        "collections", "itertools", "functools", "logging", "json", 
        "re", "tarfile", "zipfile", "pathlib", "copy", "types", 
        "weakref", "warnings", "threading", "queue", "io", "codecs",
        "pickle", "contextlib", "random"
    ]
    
    print("\n[+] Modules exposing 'os':")
    for mod_name in safe_looking_modules:
        try:
            mod = __import__(mod_name)
            if hasattr(mod, 'os') and mod.os is os:
                print(f"  - {mod_name}.os")
            if hasattr(mod, 'sys') and mod.sys is sys:
                print(f"  - {mod_name}.sys")
        except ImportError:
            pass

find_os_exporters()
