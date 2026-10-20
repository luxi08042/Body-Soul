from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from web.models.character import Character, Voice


class GetSingleCharacterView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            character_id = request.query_params.get('character_id')
            character = Character.objects.get(id=character_id, author__user=request.user)

            # 统计各音色被多少角色使用，供前端判断能否删除
            voices_raw = Voice.objects.order_by('id').annotate(
                used_count=Count('character')
            )
            voices = []
            for v in voices_raw:
                voices.append({
                    'id': v.id,
                    'name': v.name,
                    'used_count': v.used_count,
                    'deletable': v.used_count == 0,
                })

            return Response({
                'result': 'success',
                'character': {
                    'id': character.id,
                    'name': character.name,
                    'profile': character.profile,
                    'photo': character.photo.url,
                    'background_image': character.background_image.url,
                    # 角色可能没有绑定音色（音色被删除过），此时返回 None
                    'voice_id': character.voice.id if character.voice else None,
                },
                'voices': voices,
            })
        except Character.DoesNotExist:
            return Response({
                'result': '角色不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })