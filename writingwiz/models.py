# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines for those models you wish to give write DB access
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class AstarcompoQuestions(models.Model):
    questionid = models.IntegerField(db_column='questionID', primary_key=True) # Field name made lowercase.
    question = models.TextField()
    questionCategory = models.CharField(db_column='questionCategory', max_length=255) # Field name made lowercase.
    questionType = models.CharField(db_column='questionType', max_length=255) # Field name made lowercase.
    class Meta:
        db_table = 'astarcompo_questions'

class AstarcompoModelAns(models.Model):
    ansid = models.IntegerField(db_column='ansID', primary_key=True) # Field name made lowercase.
    questionid = models.ForeignKey('AstarcompoQuestions', to_field = 'questionid')
    ans = models.TextField()
    class Meta:
        db_table = 'astarcompo_model_ans'

class AstarcompoPictorial(models.Model):
    picid = models.IntegerField(db_column='picID') # Field name made lowercase.
    questionid = models.ForeignKey('AstarcompoQuestions', to_field = 'questionid')
    url = models.CharField(max_length=255)
    class Meta:
        db_table = 'astarcompo_pictorial'

class UserProfile(models.Model):
    #required by the auth model
    user = models.OneToOneField(User) 
    confirmation_code = models.CharField(max_length=1000, null=False, blank=False)
    def __str__(self):  
              return "%s's profile" % self.user

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  

post_save.connect(create_user_profile, sender=User) 


