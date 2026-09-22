from django.http import Http404
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.template import RequestContext
from django.contrib.auth import login
from django.contrib.auth import logout
from django.core.mail import send_mail

import string
import random
import hashlib

from .models import Greeting

# Create your views here.

#404
def PageNotFound(request):
	return render(request, 'error.html', {'msg': "Looks like you are browsing a page that is not existing!"})

#500
def ServerError(request):
	return render(request, 'error.html', {'msg': "Looks like the website is experiencing some problem. Check back later!"})

#403
def Forbidden(request):
	return render(request, 'error.html', {'msg': "Looks like you are not suppose to be on this page!"})

#Home Page
def index(request):
	if request.user.is_authenticated:
		usr = request.session["username"]
		superuser = request.session["superuser"] 
		return render(request, 'index.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'index.html', {'user': "", 'superuser': ""})


#Register Page
def register(request):
	if request.user.is_authenticated:
		usr = request.session["username"]
		superuser = request.session["superuser"] 
		return render(request, 'register.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'register.html', {'user': "", 'superuser': ""})

#Login Page
def login(request):
	if request.user.is_authenticated:
		usr = request.session["username"]
		superuser = request.session["superuser"] 
		return render(request, 'login.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'login.html', {'user': "", 'superuser': ""})		

#Login Page
def forgotPwd(request):
	if request.user.is_authenticated:
		usr = request.session["username"]
		superuser = request.session["superuser"] 
		return render(request, 'forgotpassword.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'forgotpassword.html', {'user': "", 'superuser': ""})		


#Functions
#Register an account with an email address and password to the server and send confirmation code to the email address specify 
def signup(request):
	errors = []
	if request.method == 'POST':
		if not request.POST.get('username'):
			errors.append('Email address is empty.')
		else:
			if '@' not in request.POST['username']:
				errors.append('Email address is not valid.')
		if not request.POST.get('password', ''):
			errors.append('Password is empty.')
		if not request.POST.get('cfmpassword', ''):
			errors.append('Confirm Password is empty.')
		if(request.POST.get('password') != request.POST.get('cfmpassword')):
			errors.append('Password does not match.')
		if User.objects.filter(username = request.POST['username']).exists(): 
			errors.append('Username already exists.')
		if not errors:
			
			user = User.objects.create_user(request.POST['username'], request.POST['username'], request.POST['password'])
			user.is_active = False
			user.save()
			confirmation_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(33))
			#p = user.UserProfile
			#p.user = user
			#p.confirmation_code = confirmation_code
			#p.save()
			title = "Writingwiz Account Confirmation"
			message = "Welcome to Writingwiz,\n\nPlease click the link below to activate your account\n\n" + "http://" + request.get_host() + "/verifyAccount/?code=" + str(confirmation_code) + "&user=" + user.username + "\n\nBest Regards,\nWritingwiz admin"
			send_mail(title, message, 'astarcompo@gmail.com', [user.email], fail_silently=False)
			content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>A notification had been send to your email account. </strong><br/> Please verify your account by clicking on the link provided in the notification. If you cannot recieved the notification, click on the "Resend Notification" Button.</div>'
			con = True
			return render(request, 'confirmation.html', {'con': con, 'content': content, 'code': confirmation_code, 'email': request.POST['username'], 'user': "", 'superuser': ""})
		else:
			return render(request, 'register.html', {'errors': errors, 'username': request.POST['username'], 'password': request.POST['password'], 'cfmpassword': request.POST['cfmpassword'], 'user': "", 'superuser': ""})
	else:
		return HttpResponseRedirect('/403/')	
		
def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

