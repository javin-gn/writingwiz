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
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout

import hashlib

from django.utils.html import format_html, format_html_join

from django.shortcuts import get_object_or_404
from django.contrib.auth.signals import user_logged_in

from .models import Greeting, Questions, LearningVideo, Vocabulary, Phrase
from .grading import grade_essay

#Keep the session keys the rest of the app reads in sync for every login path,
#including allauth's Google sign-in, which never goes through our own login() view.
def _sync_session_on_login(sender, request, user, **kwargs):
	request.session['username'] = user.username
	request.session['superuser'] = user.is_superuser

user_logged_in.connect(_sync_session_on_login)

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
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "") 
		return render(request, 'index.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'index.html', {'user': "", 'superuser': ""})


#Register Page
def register(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "") 
		return render(request, 'register.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'register.html', {'user': "", 'superuser': ""})

#Login Page
def login(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
		return render(request, 'login.html', {'user': usr, 'superuser': superuser})

	next_url = request.GET.get('url', '/')
	errors = []
	username = ''

	if request.method == 'POST':
		username = request.POST.get('username', '')
		password = request.POST.get('password', '')

		user = authenticate(request, username=username, password=password)
		if user is not None:
			auth_login(request, user)
			request.session['username'] = user.username
			request.session['superuser'] = user.is_superuser
			return HttpResponseRedirect(next_url or '/')
		elif User.objects.filter(username=username, is_active=False).exists():
			errors.append('This account has been deactivated.')
		else:
			errors.append('Incorrect email or password.')

	return render(request, 'login.html', {
		'errors': errors,
		'username': username,
		'next': next_url,
		'user': '',
		'superuser': '',
	})

#Logout
def logout(request):
	auth_logout(request)
	request.session.flush()
	return HttpResponseRedirect('/')

#Login Page
def forgotPwd(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "") 
		return render(request, 'forgotpassword.html', {'user': usr, 'superuser': superuser})
	else:
		return render(request, 'forgotpassword.html', {'user': "", 'superuser': ""})		


#Functions
#Register an account with an email address and password, active immediately (no email verification)
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
			user.is_active = True
			user.save()
			auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
			return HttpResponseRedirect('/')
		else:
			return render(request, 'register.html', {'errors': errors, 'username': request.POST['username'], 'password': request.POST['password'], 'cfmpassword': request.POST['cfmpassword'], 'user': "", 'superuser': ""})
	else:
		return HttpResponseRedirect('/403/')

def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

def _category_link_list(qtype):
	categories = (
		Questions.objects.filter(questionType=qtype)
		.order_by('questionCategory')
		.values_list('questionCategory', flat=True)
		.distinct()
	)
	return format_html(
		'<ul class="list-unstyled">{}</ul>',
		format_html_join(
			'',
			'<li><a href="#" onclick="loadQuestions(\'{}\', \'{}\'); return false;">{}</a></li>',
			((c, qtype, c) for c in categories),
		),
	)


#Continuous Writing browse page
def continuous(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	return render(request, 'continuous.html', {
		'catlist': _category_link_list('Continuous'),
		'addQuestionBtn': '',
		'content': '<div id="questions"><p>Select a category on the left to browse questions.</p></div>',
		'user': usr,
		'superuser': superuser,
	})

#Situational Writing browse page
def situational(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	return render(request, 'situational.html', {
		'list': _category_link_list('Situational'),
		'content': '<div id="questions"><p>Select a category on the left to browse questions.</p></div>',
		'user': usr,
		'superuser': superuser,
	})

#Simple static informational page
def guides(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""
	return render(request, 'guides.html', {'user': usr, 'superuser': superuser})

#Download Packages page - no packages have been re-added yet after the data migration
def packages(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""
	return render(request, 'packages.html', {
		'content': '<p>No downloadable packages are available yet.</p>',
		'user': usr,
		'superuser': superuser,
	})

#List of learning videos
def videolist(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	videos = LearningVideo.objects.order_by('title')
	content = format_html(
		'<table id="vtable" class="table"><thead><tr><th>Title</th><th>Views</th></tr></thead><tbody>{}</tbody></table>',
		format_html_join(
			'',
			'<tr><td><a href="/watch_video/{}/">{}</a></td><td>{}</td></tr>',
			((v.id, v.title, v.noOfViews or 0) for v in videos),
		),
	)

	return render(request, 'videos.html', {
		'content': content,
		'user': usr,
		'superuser': superuser,
	})

#Watch a single video, counting the view
def watch_video(request, video_id):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	video = get_object_or_404(LearningVideo, pk=video_id)
	video.noOfViews = (video.noOfViews or 0) + 1
	video.save(update_fields=['noOfViews'])

	return render(request, 'watch_video.html', {
		'title': video.title,
		'url': video.url,
		'content': '',
		'user': usr,
		'superuser': superuser,
	})

#Vivid Vocabulary Listing (vocabulary + phrases combined)
def vp(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	entries = sorted(
		[(v.vocabulary, v.category) for v in Vocabulary.objects.all()]
		+ [(p.phrase, p.category) for p in Phrase.objects.all()],
		key=lambda e: (e[1], e[0]),
	)
	content = format_html(
		'<table id="vptable" class="table"><thead><tr><th>Word / Phrase</th><th>Category</th></tr></thead><tbody>{}</tbody></table>',
		format_html_join('', '<tr><td>{}</td><td>{}</td></tr>', entries),
	)

	return render(request, 'vp.html', {
		'content': content,
		'user': usr,
		'superuser': superuser,
	})

#Standalone rule-based PSLE essay grader - not an AI/LLM assessment, see grading.py
def essay_grader(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	questions = Questions.objects.order_by('questionType', 'questionCategory', 'questionid')

	result = None
	essay_text = ''
	qtype = 'Continuous'
	question_id = ''

	if request.method == 'POST':
		essay_text = request.POST.get('essay', '')
		qtype = request.POST.get('qtype', 'Continuous')
		question_id = request.POST.get('question_id', '')

		question_text = ''
		if question_id:
			question = Questions.objects.filter(questionid=question_id).first()
			if question:
				qtype = question.questionType
				question_text = question.question

		result = grade_essay(essay_text, qtype=qtype, question_text=question_text)

	return render(request, 'essay_grader.html', {
		'questions': questions,
		'result': result,
		'essay_text': essay_text,
		'qtype': qtype,
		'question_id': question_id,
		'user': usr,
		'superuser': superuser,
	})

#AJAX endpoint used by continuous.html / situational.html to load a filtered question list
def questions_browse(request):
	qtype = request.GET.get('type', '')
	category = request.GET.get('query', '')

	questions = Questions.objects.filter(questionType=qtype)
	if category:
		questions = questions.filter(questionCategory=category)
	questions = questions.order_by('questionid')

	return render(request, 'questions_fragment.html', {'questions': questions})

