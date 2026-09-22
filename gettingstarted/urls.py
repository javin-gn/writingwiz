from django.urls import re_path, path

from django.contrib import admin
admin.autodiscover()

import writingwiz.views

urlpatterns = [
    re_path(r'^$', writingwiz.views.index, name='index'),
	re_path(r'^register', writingwiz.views.register, name='register'),
	re_path(r'^404', writingwiz.views.PageNotFound, name='PageNotFound'),
	re_path(r'^500', writingwiz.views.ServerError, name='ServerError'),
	re_path(r'^403', writingwiz.views.Forbidden, name='Forbidden'),
	re_path(r'^signup', writingwiz.views.signup, name='signup'),
	re_path(r'^login', writingwiz.views.login, name='login'),
	re_path(r'^forgotpassword', writingwiz.views.forgotPwd, name='forgotPwd'),
    re_path(r'^db', writingwiz.views.db, name='db'),
    path('admin/', admin.site.urls),
]
