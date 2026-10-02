from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

def _next_id(model, field):
    from django.db.models import Max
    current_max = model.objects.aggregate(m=Max(field))['m']
    return (current_max or 0) + 1

def _next_question_id():
    return _next_id(Questions, 'questionid')

def _next_ans_id():
    return _next_id(ModelAns, 'ansid')

def _next_pic_id():
    return _next_id(Pictorial, 'picid')

class Questions(models.Model):
    questionid = models.IntegerField(db_column='questionID', primary_key=True, default=_next_question_id) # Field name made lowercase.
    question = models.TextField()
    questionCategory = models.CharField(db_column='questionCategory', max_length=255) # Field name made lowercase.
    questionType = models.CharField(db_column='questionType', max_length=255) # Field name made lowercase.
    theme = models.CharField(max_length=255, blank=True, default='')
    class Meta:
        db_table = 'questions'
    def __str__(self):
        return f'#{self.questionid} [{self.questionType}/{self.questionCategory}] {self.question[:60]}'

class ModelAns(models.Model):
    ansid = models.IntegerField(db_column='ansID', primary_key=True, default=_next_ans_id) # Field name made lowercase.
    questionid = models.ForeignKey(Questions, on_delete=models.CASCADE)
    ans = models.TextField()
    class Meta:
        db_table = 'model_ans'
    def __str__(self):
        return f'Answer #{self.ansid} for question #{self.questionid_id}'

class Pictorial(models.Model):
    picid = models.IntegerField(db_column='picID', default=_next_pic_id) # Field name made lowercase.
    questionid = models.ForeignKey(Questions, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    class Meta:
        db_table = 'pictorial'
    def __str__(self):
        return f'Picture #{self.picid} for question #{self.questionid_id}'

class LearningVideo(models.Model):
    url = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    noOfViews = models.IntegerField(db_column='noOfViews', null=True, blank=True, default=0)
    dateCreated = models.DateTimeField(db_column='dateCreated', null=True, blank=True, auto_now_add=True)
    class Meta:
        db_table = 'learningvideos'
    def __str__(self):
        return self.title or f'Video #{self.id}'

class VpCategory(models.Model):
    category = models.CharField(max_length=255, primary_key=True)
    class Meta:
        db_table = 'vpcat'
        verbose_name_plural = 'VP categories'
    def __str__(self):
        return self.category

class Vocabulary(models.Model):
    vocabulary = models.CharField(max_length=255, primary_key=True)
    category = models.CharField(max_length=255)
    theme = models.CharField(max_length=255, blank=True)
    class Meta:
        db_table = 'vocabularies'
        verbose_name_plural = 'Vocabularies'
    def __str__(self):
        return self.vocabulary

class Phrase(models.Model):
    phrase = models.CharField(max_length=255, primary_key=True)
    category = models.CharField(max_length=255)
    theme = models.CharField(max_length=255, blank=True)
    class Meta:
        db_table = 'phrases'
    def __str__(self):
        return self.phrase

class EssayAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='essay_attempts')
    question = models.ForeignKey(Questions, on_delete=models.CASCADE, null=True, blank=True, related_name='essay_attempts')
    qtype = models.CharField(max_length=20)
    essay_text = models.TextField()
    total_score = models.FloatField()
    total_max = models.FloatField()
    content_score = models.FloatField()
    content_max = models.FloatField(default=0)
    language_score = models.FloatField()
    language_max = models.FloatField(default=0)
    breakdown = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'essay_attempts'
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.user} - {self.total_score}/{self.total_max} on {self.created_at:%Y-%m-%d}'
    @property
    def percent(self):
        return round(self.total_score / self.total_max * 100) if self.total_max else 0
    @property
    def content_percent(self):
        return round(self.content_score / self.content_max * 100) if self.content_max else 0
    @property
    def language_percent(self):
        return round(self.language_score / self.language_max * 100) if self.language_max else 0

class VividVocabularyUsage(models.Model):
    """One row per vivid vocabulary/phrase bank entry detected in a graded
    essay - powers the per-category vivid vocabulary leaderboard. A word
    repeated several times in one essay is still only recorded once per
    attempt (grading.py's detection is membership-based, not a count), so
    this can't be gamed by spamming the same word."""
    KIND_CHOICES = [
        ('vocabulary', 'Vocabulary'),
        ('phrase', 'Phrase'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vivid_vocabulary_usages')
    attempt = models.ForeignKey(EssayAttempt, on_delete=models.CASCADE, related_name='vivid_vocabulary_usages')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    text = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'vivid_vocabulary_usages'
    def __str__(self):
        return f'{self.user} used "{self.text}" ({self.category})'

class SiteSettings(models.Model):
    """Singleton (always pk=1) holding site-wide toggles managed from /manage/."""
    registration_enabled = models.BooleanField(default=True)
    google_signin_enabled = models.BooleanField(default=True)
    class Meta:
        db_table = 'site_settings'
    def __str__(self):
        return 'Site Settings'
    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class Announcement(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
    ]
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']
    def __str__(self):
        return self.title

class UserProfile(models.Model):
    #required by the auth model
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    confirmation_code = models.CharField(max_length=1000, null=False, blank=False)
    def __str__(self):  
              return "%s's profile" % self.user

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  

post_save.connect(create_user_profile, sender=User) 