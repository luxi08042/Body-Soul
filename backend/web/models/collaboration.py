from django.db import models
from django.utils.timezone import now

from web.models.character import Character
from web.models.user import UserProfile


class MultiAgentRoom(models.Model):
    FLOW_CHOICES = [('round_robin', '轮流发言'), ('moderated', '主持人串联'), ('free', '自由讨论')]
    ORDER_CHOICES = [('configured', '按配置顺序'), ('round_robin', '循环轮换'), ('random', '随机发言')]
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='multi_agent_rooms')
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=500, blank=True, default='')
    system_prompt = models.TextField(max_length=20000, blank=True, default='')
    model_name = models.CharField(
        max_length=80,
        default='deepseek-v4.1-flash',
        help_text='留空则使用项目 .env 中实际可用的模型',
    )
    agent_count = models.PositiveSmallIntegerField(default=2)
    interval_seconds = models.PositiveSmallIntegerField(default=0)
    flow_mode = models.CharField(max_length=20, choices=FLOW_CHOICES, default='round_robin')
    turn_order = models.CharField(max_length=20, choices=ORDER_CHOICES, default='configured')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class MultiAgentParticipant(models.Model):
    room = models.ForeignKey(MultiAgentRoom, on_delete=models.CASCADE, related_name='participants')
    character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='multi_agent_participants'
    )
    display_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=80, blank=True, default='')
    api_base = models.CharField(max_length=500, blank=True, default='', help_text='可选，留空使用系统 API_BASE')
    api_key = models.CharField(max_length=500, blank=True, default='', help_text='可选，后台保存，不会返回给前端')
    use_system_api = models.BooleanField(default=True, help_text='使用系统 API_KEY/API_BASE')
    system_prompt = models.TextField(max_length=10000, blank=True, default='')
    order_number = models.PositiveSmallIntegerField(default=0)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['order_number', 'id']

    def __str__(self):
        return self.display_name


class MultiAgentMessage(models.Model):
    SPEAKER_CHOICES = [('human', '用户'), ('agent', 'Agent'), ('system', '系统')]
    room = models.ForeignKey(MultiAgentRoom, on_delete=models.CASCADE, related_name='messages')
    participant = models.ForeignKey(MultiAgentParticipant, on_delete=models.SET_NULL, null=True, blank=True)
    speaker_type = models.CharField(max_length=10, choices=SPEAKER_CHOICES, default='human')
    speaker_name = models.CharField(max_length=100)
    content = models.TextField(max_length=20000)
    turn_number = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.speaker_name} - {self.content[:30]}'