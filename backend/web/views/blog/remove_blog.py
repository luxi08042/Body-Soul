from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.blog import Blog
from web.models.user import UserProfile


class RemoveBlogView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            blog_id = request.data.get('blog_id')

            blog = Blog.objects.get(id=blog_id, author=user_profile)

            # 先删封面文件，再删记录
            if blog.cover_photo:
                blog.cover_photo.delete(save=False)
            blog.delete()

            return Response({
                'result': 'success',
            })
        except Blog.DoesNotExist:
            return Response({
                'result': '博客不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })