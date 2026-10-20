from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response

from web.models.blog import Blog
from web.models.user import UserProfile
from web.views.blog.serializers import serialize_blog


class GetUserBlogListView(APIView):
    """个人空间用：按 user_id 分页查询某个用户的博客（无需登录即可查看他人的）"""

    def get(self, request):
        try:
            items_count = int(request.query_params.get('items_count', 0))
            user_id = int(request.query_params.get('user_id'))

            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)

            # 看自己的空间显示全部；看别人的空间只显示公开博客
            is_self = (
                request.user.is_authenticated
                and request.user.id == user_id
            )

            queryset = Blog.objects.filter(author=user_profile)
            if not is_self:
                queryset = queryset.filter(is_public=True)

            blogs_raw = queryset.order_by('-id')[items_count: items_count + 20]

            return Response({
                'result': 'success',
                'user_profile': {
                    'user_id': user.id,
                    'username': user.username,
                    'profile': user_profile.profile,
                    'photo': user_profile.photo.url,
                },
                'blogs': [serialize_blog(blog) for blog in blogs_raw],
            })
        except User.DoesNotExist:
            return Response({
                'result': '用户不存在'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })