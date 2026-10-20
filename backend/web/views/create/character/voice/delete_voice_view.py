from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.character import Voice
from web.views.create.character.voice.custom.voice_api import delete_voice as delete_remote_voice


class DeleteVoiceView(APIView):
    """删除音色。

    正在被角色使用的音色不允许删除——否则角色的音色会失效。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            voice_id = request.data.get('voice_id')
            if not voice_id:
                return Response({'result': '缺少音色 id'})

            voice = Voice.objects.filter(id=voice_id).first()
            if not voice:
                return Response({'result': '音色不存在'})

            used_count = voice.character_set.count()
            if used_count > 0:
                return Response({
                    'result': f'「{voice.name}」正被 {used_count} 个角色使用，无法删除'
                })

            # 先删远端语音服务里的数据，失败也不阻塞本地删除
            remote_ok = True
            if voice.voice_id:
                try:
                    delete_remote_voice(voice.voice_id)
                except Exception:
                    remote_ok = False

            name = voice.name
            voice.delete()

            return Response({
                'result': 'success',
                'name': name,
                'remote_synced': remote_ok,
            })
        except Voice.DoesNotExist:
            return Response({'result': '音色不存在'})
        except Exception:
            return Response({'result': '系统异常，请稍后重试'})