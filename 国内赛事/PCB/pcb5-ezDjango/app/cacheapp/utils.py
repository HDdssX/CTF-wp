import os
import hashlib
import zlib
import pickle
from django.http import JsonResponse
from django.conf import settings

def json_success(message, **extra):
    return JsonResponse({"status": "success", "message": message, **extra})

def json_error(message, **extra):
    return JsonResponse({"status": "error", "message": message, **extra})

def cache_dir():
    return settings.CACHES["default"]["LOCATION"]

def cache_filename(key: str) -> str:
    return f"{hashlib.md5(key.encode()).hexdigest()}.djcache"

def read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def write_file_chunks(file_obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb+") as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

def try_decompress_and_unpickle(content: bytes):
    try:
        decompressed = zlib.decompress(content)
        data = pickle.loads(decompressed)
        return data, None
    except Exception as e:
        return None, str(e)