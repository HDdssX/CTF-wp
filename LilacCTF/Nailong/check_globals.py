
import logging
import tarfile
import zipfile

def check(name, func):
    try:
        if hasattr(func, '__globals__'):
            g = func.__globals__
            if 'os' in g:
                print(f"{name} -> Has 'os'")
            else:
                print(f"{name} -> No 'os'")
        else:
            print(f"{name} -> No __globals__")
    except Exception as e:
        print(f"{name} -> Error: {e}")

check("logging.getLogger", logging.getLogger)
check("tarfile.open", tarfile.open)
check("zipfile.ZipFile", zipfile.ZipFile)
