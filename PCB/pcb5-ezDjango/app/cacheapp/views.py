import os
import base64
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.conf import settings
import hashlib
import json
from .utils import json_success, json_error, cache_dir, cache_filename, read_file_bytes, write_file_chunks
from django.utils.html import escape
from django.utils.html import format_html


@cache_page(60)
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def generate_page(request):
    if request.method == "POST":
        intro = str(request.POST.get('intro', ''))
        user = request.user if request.user.is_authenticated else 'Guest'
        blacklist = ['admin', 'config.']
        for word in blacklist:
            if word in intro:
                return HttpResponse("can't be as admin")
        outer_html = ('<h1>hello {user}</h1></p><h3>' + intro + '</h3>').format(user=request.user)
        f = request.FILES.get("file", None)
        filename = request.POST.get('filename', '') if request.POST.get('filename') else (f.name if f else '')
        
        if not f:
            return HttpResponse("❌ 没有上传文件")
        
        if not filename:
            filename = f.name
        if '.py' in filename:
            return HttpResponse("❌ 不允许上传.py文件")
        try:
            static_dir = os.path.join(settings.BASE_DIR, 'static', 'uploads')
            os.makedirs(static_dir, exist_ok=True)
            filepath = os.path.join(static_dir, filename)
            write_file_chunks(f, filepath)
            
            return HttpResponse(outer_html + f"</p><p>✅ 文件已上传: /static/uploads/{filename}</p>")
            
        except Exception as e:
            return HttpResponse(f"❌ 文件上传失败: {str(e)}")
    
    return render(request, 'generate.html')




@csrf_exempt
def upload_payload(request):
    if request.method == "POST":
        f = request.FILES.get("file", None)
        if not f:
            return json_error('No file uploaded')
        filename = request.POST.get('filename', f.name)
        if not filename.endswith('.cache'):
            return json_error('Only .cache files are allowed')
        try:
            temp_dir = '/tmp'
            filepath = os.path.join(temp_dir, filename)
            write_file_chunks(f, filepath)
            return json_success('File uploaded', filepath=filepath)
        except Exception as e:
            return json_error(str(e))
    
    return render(request, 'upload.html')


@csrf_exempt
def copy_file(request):
    if request.method == "POST":
        src = request.POST.get('src', '')
        dst = request.POST.get('dst', '')
        if not src or not dst:
            return json_error('Source and destination required')
        try:
            if not os.path.exists(src):
                return json_error('Source file not found')
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            content = read_file_bytes(src)
            with open(dst, 'wb') as dest_file:
                dest_file.write(content)
            return json_success('File copied', src=src, dst=dst)
        except Exception as e:
            return json_error(str(e))
    
    return render(request, 'copy.html')


@csrf_exempt
def cache_viewer(request):
    if request.method == "POST":
        cache_key = request.POST.get('key', '')
        if not cache_key:
            return json_error('Cache key required')
        try:
            path = os.path.join(cache_dir(), cache_filename(cache_key))
            if os.path.exists(path):
                content = read_file_bytes(path)
                return json_success('Read cache raw', cache_path=path, raw_content=content.hex())
            return json_error(f'Cache file not found: {path}')
        except Exception as e:
            return json_error(str(e))
    
    return render(request, 'cache_viewer.html')


def profile(request):
    return render(request, 'profile.html', {'user': request.user})
@csrf_exempt
def cache_trigger(request):
    if request.method == "POST":
        key = request.POST.get('key', '') or settings.CACHE_KEY
        try:
            val = cache.get(key, None)
            if isinstance(val, (bytes, bytearray)):
                return json_success('Triggered', value_b64=base64.b64encode(val).decode())
            return json_success('Triggered', value=str(val))
        except Exception as e:
            return json_error(str(e))
    return json_error('POST required')