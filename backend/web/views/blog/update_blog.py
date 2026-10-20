from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.blog import Blog, Tag
from web.models.user import UserProfile
from web.views.blog.create_blog import parse_tags
from web.views.blog.serializers import serialize_blog


class UpdateBlogView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            blog_id = request.data.get('blog_id')
            title = request.data.get('title').strip()
            content = request.data.get('content').strip()
            cover_photo = request.FILES.get('cover_photo', None)
            tag_names = parse_tags(request.data.get('tags'))

            if not title:
                return Response({
                    'result': '标题不能为空'
                })
            if not content:
                return Response({
                    'result': '正文不能为空'
                })

            blog = Blog.objects.get(id=blog_id, author=user_profile)

            blog.title = title
            blog.content = content
            # 传了 is_public 才更新，支持在不改正文的情况下切换公开/私密
            if 'is_public' in request.data:
                blog.is_public = str(request.data.get('is_public')).lower() != 'false'
            if cover_photo:
                # 先记下旧文件路径。注意：不能直接对 old_cover 调 delete()，
                # 因为它与 blog.cover_photo 是同一个 FieldFile 对象，
                # delete() 会把模型字段一并清空，导致保存后封面变成空
                old_name = blog.cover_photo.name if blog.cover_photo else ''
                blog.cover_photo = cover_photo

            blog.save()

            # 保存成功后再删旧文件（用存储层删除，不触碰模型字段）
            if cover_photo and old_name:
                try:
                    blog.cover_photo.storage.delete(old_name)
                except Exception:
                    # 旧文件清理失败不影响本次更新
                    pass

            # 全量覆盖标签
            blog.tags.clear()
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                blog.tags.add(tag)

            return Response({
                'result': 'success',
                # 直接把更新后的博客返回给前端，避免前端二次请求导致封面显示不及时
                'blog': serialize_blog(blog),
            })
        except Blog.DoesNotExist:
            return Response({
                'result': '博客不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })