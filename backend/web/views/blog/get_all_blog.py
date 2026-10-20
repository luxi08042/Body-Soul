from rest_framework.views import APIView
from rest_framework.response import Response

from web.models.blog import Blog
from web.views.blog.serializers import serialize_blog


class GetAllBlogsView(APIView):
    def get(self, request):
        try:
            # 博客大厅只展示公开博客
            blogs = Blog.objects.filter(is_public=True)

            return Response({
                'result': 'success',
                'blogs': [serialize_blog(blog) for blog in blogs],
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })