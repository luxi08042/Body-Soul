"""博客相关的序列化函数。"""


def serialize_blog(blog):
    """把 Blog 模型转成前端可直接使用的字典。"""
    return {
        'id': blog.id,
        'title': blog.title,
        'content': blog.content,
        'cover_photo': blog.cover_photo.url if blog.cover_photo else '',
        'author_id': blog.author.user_id,
        'username': blog.author.user.username,
        'photo': blog.author.photo.url,
        'profile': blog.author.profile,
        'tags': [tag.name for tag in blog.tags.all()],
        'is_public': blog.is_public,
        'create_time': blog.create_time.strftime('%Y-%m-%d %H:%M:%S'),
    }
