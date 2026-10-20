from rest_framework.views import APIView
from rest_framework.response import Response

from web.models.blog import Blog
from web.views.blog.serializers import serialize_blog


class GetBlogDetailView(APIView):
    def get(self, request, blog_id):
        try:
            blog = Blog.objects.get(id=blog_id)

            # 私密博客只有作者本人能查看，防止通过直链访问
            if not blog.is_public:
                is_author = (
                    request.user.is_authenticated
                    and blog.author.user_id == request.user.id
                )
                if not is_author:
                    return Response({
                        'result': '该博客为私密内容，无法查看'
                    })

            return Response({
                'result': 'success',
                'blog': serialize_blog(blog),
            })
        except Blog.DoesNotExist:
            return Response({
                'result': '博客不存在'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })