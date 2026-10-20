"""博客增加公开/私有字段。

- is_public=True：所有人可见（默认，保持原有行为）
- is_public=False：仅作者自己在「我的博客」中可见
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0012_character_voice_set_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="blog",
            name="is_public",
            # default=True 保证已有博客迁移后全部是公开的，不改变原有行为
            field=models.BooleanField(default=True, verbose_name="是否公开"),
        ),
    ]
