from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.blog import Blog
from web.models.user import UserProfile
from web.views.blog.serializers import serialize_blog


class GetMyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)

            # 我的博客包含公开与私密全部
            blogs = Blog.objects.filter(author=user_profile)

            return Response({
                'result': 'success',
                'blogs': [serialize_blog(blog) for blog in blogs],
            })
        except UserProfile.DoesNotExist:
            return Response({
                'result': '用户信息不存在'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })