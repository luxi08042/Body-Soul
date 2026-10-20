import uuid

from django.db import models
from django.utils import timezone

from web.models.user import UserProfile


def blog_cover_upload_to(instance, filename):
    # 文件名可能没有扩展名（如某些浏览器/客户端），需做兜底
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    if not ext or len(ext) > 5:
        ext = 'jpg'
    filename = f'{uuid.uuid4().hex[:10]}.{ext}'
    return f'blog/cover/{instance.author.user_id}_{filename}'


class Tag(models.Model):
    name = models.CharField(max_length=10, unique=True, verbose_name='标签名')

    def __str__(self):
        return self.name


class Blog(models.Model):
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='正文')
    cover_photo = models.ImageField(upload_to=blog_cover_upload_to, blank=True, null=True, verbose_name='文章封面')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签')
    # 公开博客所有人可见；私密博客仅作者自己在"我的博客"里能看到
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    create_time = models.DateTimeField(default=timezone.now)
    update_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-create_time']  # 按照时间倒序

    def __str__(self):
        return f'{self.title} - {self.author.user.username} - {timezone.localtime(self.create_time).strftime("%Y-%m-%d %H:%M:%S")}'