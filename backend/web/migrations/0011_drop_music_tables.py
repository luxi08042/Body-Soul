"""删除整个音乐模块的数据表。

音乐模块（含上传歌曲、听歌房间、外部元数据引用、榜单）已整体下线，
这里一次性移除相关表。多智能体与博客相关的表不受影响。
"""

from django.db import migrations

# 先删有外键指向的表，避免外键约束报错
TABLES_IN_ORDER = [
    # 关联/中间表
    ("web", "musicsave"),
    ("web", "playlistexternalsong"),
    ("web", "playlistsave"),
    ("web", "musicrecommend"),
    ("web", "externalsongsave"),
    ("web", "externalalbumsave"),
    ("web", "listeningentry"),
    ("web", "listeningmember"),
    # 主表
    ("web", "listeningroom"),
    ("web", "externalsong"),
    ("web", "externalalbum"),
    ("web", "playlistsong"),
    ("web", "playlist"),
    ("web", "song"),
]


def drop_music_tables(apps, schema_editor):
    """直接 DROP 表，绕过模型层的历史约束问题。

    先关掉外键检查（SQLite 默认禁止删被引用的表），再逐个 DROP。
    """
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute('PRAGMA foreign_keys = OFF;')
        try:
            for app_label, table in TABLES_IN_ORDER:
                cursor.execute(f'DROP TABLE IF EXISTS "{app_label}_{table}";')
        finally:
            if connection.vendor == 'sqlite':
                cursor.execute('PRAGMA foreign_keys = ON;')


def noop(apps, schema_editor):
    """反向操作：空实现。

    音乐模块的表包含已删除的字段与外键，精确逆向重建风险高；
    如需恢复请从备份还原数据库。
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0010_alter_playlist_is_public_externalalbum_and_more"),
    ]

    operations = [
        migrations.RunPython(drop_music_tables, noop),
    ]