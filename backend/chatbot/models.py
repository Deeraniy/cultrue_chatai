from django.db import models

# Create your models here.

class LiteratureEmotionSummary(models.Model):
    liter_id = models.IntegerField(primary_key=True)
    liter_name = models.CharField(max_length=100)
    total_comments = models.IntegerField()
    positive_count = models.IntegerField()
    neutral_count = models.IntegerField()
    negative_count = models.IntegerField()
    positive_ratio = models.DecimalField(max_digits=8, decimal_places=3)

    class Meta:
        db_table = 'literature_emotion_summary'
        managed = False  # 该表为数据库已有的汇总表，不由Django迁移管理

class Literature(models.Model):
    liter_id = models.IntegerField(primary_key=True)
    liter_name = models.CharField(max_length=100)
    description = models.TextField()
    type_id = models.IntegerField()
    text = models.TextField(null=True, blank=True)  # 作品片段或内容
    class Meta:
        db_table = 'literature'
        managed = False

# 用户阅读计划模型
class ReadingPlan(models.Model):
    user_id = models.CharField(max_length=100)
    book = models.CharField(max_length=200)  # 新增字段
    start_date = models.DateField()           # 新增字段
    end_date = models.DateField()             # 新增字段
    plan_content = models.TextField()
    current_progress = models.CharField(max_length=100, default='未开始')
    is_active = models.BooleanField(default=True)
    last_update = models.DateTimeField(auto_now=True)
    initial_emotion = models.CharField(max_length=20, blank=True, null=True)
    initial_emotion_score = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'reading_plan'

# 用户每日情绪与进度记录模型
class DailyStatus(models.Model):
    user_id = models.CharField(max_length=100)
    plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE)
    book = models.CharField(max_length=200)
    date = models.DateField()
    actual_progress = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    emotion = models.CharField(max_length=20, blank=True, null=True)
    emotion_score = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'daily_status'

class UserEmotionHistory(models.Model):
    user_id = models.CharField(max_length=100)
    date = models.DateField()
    source = models.CharField(max_length=50)  # 如 '打卡', '日记', '对话', '推荐'
    plan = models.ForeignKey(ReadingPlan, on_delete=models.SET_NULL, null=True, blank=True)
    book = models.CharField(max_length=200, blank=True, null=True)
    emotion = models.CharField(max_length=20, blank=True, null=True)
    emotion_score = models.FloatField(blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_emotion_history'

# 对话会话模型
class Conversation(models.Model):
    user_id = models.CharField(max_length=100)
    plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default='新对话')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'conversation'
        ordering = ['-updated_at']

# 对话消息模型
class Message(models.Model):
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', '助手'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message'
        ordering = ['created_at']
