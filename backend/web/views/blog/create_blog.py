from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.blog import Blog, Tag
from web.models.user import UserProfile


def parse_tags(raw):
    """标签既可能是 JSON 数组字符串，也可能是重复传的表单字段，统一解析成字符串列表"""
    import json

    tags = []
    if raw is None:
        return tags

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return tags
        if text.startswith('['):
            try:
                raw = json.loads(text)
            except ValueError:
                raw = [text]
        else:
            # 逗号或空格分隔的纯文本
            raw = [t for t in text.replace('，', ',').replace(' ', ',').split(',') if t]
    elif isinstance(raw, (list, tuple)):
        raw = list(raw)

    for item in raw:
        name = str(item).strip()
        if name and name not in tags:
            tags.append(name)

    return tags


class CreateBlogView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            title = request.data.get('title').strip()
            content = request.data.get('content').strip()
            cover_photo = request.FILES.get('cover_photo', None)
            tag_names = parse_tags(request.data.get('tags'))

            # 不传该字段时默认公开，保持原有行为
            is_public = str(request.data.get('is_public', 'true')).lower() != 'false'

            if not title:
                return Response({
                    'result': '标题不能为空'
                })
            if not content:
                return Response({
                    'result': '正文不能为空'
                })

            blog = Blog.objects.create(
                author=user_profile,
                title=title,
                content=content,
                cover_photo=cover_photo,
                is_public=is_public,
            )

            # 标签不存在则自动创建
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                blog.tags.add(tag)

            return Response({
                'result': 'success',
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })