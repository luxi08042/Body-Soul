from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.character import Voice


class GetVoiceList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # 统计每个音色被多少角色使用，前端据此决定是否允许删除
            voices_raw = Voice.objects.order_by('id').annotate(
                used_count=Count('character')
            )
            voices = []
            for v in voices_raw:
                voices.append({
                    'id': v.id,
                    'name': v.name,
                    'used_count': v.used_count,
                    # 正被角色使用时不允许删除，避免误删导致角色失效
                    'deletable': v.used_count == 0,
                })
            return Response({
                'result': 'success',
                'voices': voices,
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })