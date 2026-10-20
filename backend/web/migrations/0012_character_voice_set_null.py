"""把 Character.voice 的 on_delete 从 CASCADE 改为 SET_NULL。

删除音色时不再连带删除角色，只会把角色的音色置空。
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0011_drop_music_tables"),
    ]

    operations = [
        migrations.AlterField(
            model_name="character",
            name="voice",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=models.SET_NULL,
                to="web.voice",
            ),
        ),
    ]
