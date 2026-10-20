"""阿里云百炼（DashScope）音色管理接口封装。

三个动作对应三个函数：create_voice / list_voice / delete_voice。
"""

import os

import requests

# 请求超时（秒）
TIMEOUT = 60


def _post_voice_api(action, payload):
    """调用百炼音色管理接口，返回解析后的 json。"""
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "voice-enrollment",
        "input": {"action": action, **payload},
    }
    response = requests.post(
        os.getenv('VOICE_URL'), headers=headers, json=data, timeout=TIMEOUT
    )
    return response.json()


def create_voice(voice_url, prefix):
    """用一段音频复刻音色。

    voice_url 是云端能回拉到的音频地址，prefix 最长 10 个字符。
    """
    return _post_voice_api('create_voice', {
        "target_model": "cosyvoice-v3-flash",
        "prefix": prefix,
        "url": voice_url,
    })


def list_voice():
    """列出云端已有的音色。"""
    return _post_voice_api('list_voice', {
        "page_size": 100,
        "page_index": 0,
    })


def delete_voice(voice_id):
    """删除云端音色。"""
    return _post_voice_api('delete_voice', {
        "voice_id": voice_id,
    })
