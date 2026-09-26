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