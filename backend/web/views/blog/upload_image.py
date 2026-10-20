import os
import uuid

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


class BlogImageUploadView(APIView):
    """供 markdown 编辑器插入图片使用，返回可直接引用的 url"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            image = request.FILES.get('image')
            if not image:
                return Response({
                    'result': '图片不能为空'
                })

            ext = os.path.splitext(image.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return Response({
                    'result': '只支持 jpg、png、gif、webp 格式的图片'
                })

            filename = f'{uuid.uuid4().hex[:10]}{ext}'
            relative_path = f'blog/images/{request.user.id}_{filename}'
            absolute_path = settings.MEDIA_ROOT / relative_path

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, 'wb') as f:
                for chunk in image.chunks():
                    f.write(chunk)

            return Response({
                'result': 'success',
                'url': f'{settings.MEDIA_URL}{relative_path}',
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })