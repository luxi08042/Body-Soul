import os
import uuid

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.character import Voice
from web.views.create.character.voice.custom.voice_api import create_voice

# 百炼音色复刻支持的音频格式
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.webm'}


class CloneVoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            name = request.data.get('name', '').strip()
            audio = request.FILES.get('audio')

            if not name:
                return Response({
                    'result': '音色名称不能为空'
                })
            if not audio:
                return Response({
                    'result': '音频文件不能为空'
                })

            ext = os.path.splitext(audio.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return Response({
                    'result': f'不支持的音频格式{ext}，请上传 mp3、wav、m4a 格式'
                })

            # 保存录音到 media，供云端按 url 拉取
            filename = f'{uuid.uuid4().hex[:10]}{ext}'
            relative_path = f'voice/clone/{request.user.id}_{filename}'
            absolute_path = settings.MEDIA_ROOT / relative_path

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, 'wb') as f:
                for chunk in audio.chunks():
                    f.write(chunk)

            # 百炼的服务器要能回拉这个音频，所以必须是它能访问到的公网地址。
            # 本地开发时 127.0.0.1 云端访问不到，需要配一个公网可达的域名（可用环境变量指定）。
            public_base = os.getenv('PUBLIC_BASE_URL', '').strip().rstrip('/')
            if not public_base:
                if settings.DEBUG:
                    # 本地开发：优先用环境变量，否则退回到请求头推断
                    host = request.get_host()
                    scheme = request.scheme
                    public_base = f'{scheme}://{host}'
                else:
                    public_base = request.build_absolute_uri('/')[:-1]

            audio_url = f'{public_base}/media/{relative_path}'

            # 百炼规定 prefix 最长 10 个字符
            prefix = f'v{uuid.uuid4().hex[:9]}'
            result = create_voice(audio_url, prefix)

            # 百炼返回体形如 {"output": {"voice_id": "...", "task_id": "..."}}
            output = result.get('output') or {}
            voice_id = output.get('voice_id')
            if not voice_id:
                # 把云端的具体原因透出来，方便排查
                message = result.get('message') or '音色复刻失败，请稍后重试'
                return Response({
                    'result': message,
                    'detail': result,
                })

            voice = Voice.objects.create(
                name=name,
                voice_id=voice_id,
            )

            return Response({
                'result': 'success',
                'voice': {
                    'id': voice.id,
                    'name': voice.name,
                },
            })
        except Exception:
            return Response({
                'result': '系统异常，请稍后重试'
            })