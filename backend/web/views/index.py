import os

from django.conf import settings
from django.shortcuts import render


def get_built_assets():
    """扫描 vite 构建产物，动态拿到带哈希的 js/css 文件名。

    这样每次 npm run build 后文件名变化也不用手动改模板。
    """
    assets_dir = settings.BASE_DIR / 'static' / 'frontend' / 'assets'
    js_files = []
    css_files = []

    if assets_dir.exists():
        for filename in os.listdir(assets_dir):
            relative = f'frontend/assets/{filename}'
            if filename.endswith('.js'):
                js_files.append(relative)
            elif filename.endswith('.css'):
                css_files.append(relative)

    return {
        'vite_js_files': sorted(js_files),
        'vite_css_files': sorted(css_files),
    }


def index(request):
    return render(request, "index.html", get_built_assets())