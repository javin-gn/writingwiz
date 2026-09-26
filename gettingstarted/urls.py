from django.urls import re_path, path, include

from django.contrib import admin
admin.autodiscover()

import writingwiz.views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    re_path(r'^$', writingwiz.views.index, name='index'),
	re_path(r'^register', writingwiz.views.register, name='register'),
	re_path(r'^404', writingwiz.views.PageNotFound, name='PageNotFound'),
	re_path(r'^500', writingwiz.views.ServerError, name='ServerError'),
	re_path(r'^403', writingwiz.views.Forbidden, name='Forbidden'),
	re_path(r'^signup', writingwiz.views.signup, name='signup'),
	re_path(r'^login', writingwiz.views.login, name='login'),
	re_path(r'^logout', writingwiz.views.logout, name='logout'),
	re_path(r'^forgotpassword', writingwiz.views.forgotPwd, name='forgotPwd'),
    re_path(r'^db', writingwiz.views.db, name='db'),
    re_path(r'^continuous', writingwiz.views.continuous, name='continuous'),
    re_path(r'^questions/', writingwiz.views.questions_browse, name='questions_browse'),
    re_path(r'^situational', writingwiz.views.situational, name='situational'),
    re_path(r'^guides/', writingwiz.views.guides, name='guides'),
    re_path(r'^downloadPackages', writingwiz.views.packages, name='packages'),
    path('watch_video/<int:video_id>/', writingwiz.views.watch_video, name='watch_video'),
    re_path(r'^videolist', writingwiz.views.videolist, name='videolist'),
    re_path(r'^vp/', writingwiz.views.vp, name='vp'),
    path('grader/', writingwiz.views.essay_grader, name='essay_grader'),
    path('add_question/', writingwiz.views.add_question, name='add_question'),
    path('insert_question/', writingwiz.views.insert_question, name='insert_question'),
    path('edit_question/<int:question_id>/', writingwiz.views.edit_question, name='edit_question'),
    path('update_question/', writingwiz.views.update_question, name='update_question'),
    path('edit_answer/<int:ans_id>/', writingwiz.views.edit_answer_view, name='edit_answer'),
    path('update_answer/', writingwiz.views.update_answer, name='update_answer'),
    path('admin/', admin.site.urls),
]
