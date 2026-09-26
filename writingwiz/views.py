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

import os
import uuid

from django.conf import settings

from .models import (
	Greeting, Questions, ModelAns, Pictorial, LearningVideo, Vocabulary, Phrase,
	_next_question_id, _next_ans_id, _next_pic_id,
)
from .grading import grade_essay

#Keep the session keys the rest of the app reads in sync for every login path,
#including allauth's Google sign-in, which never goes through our own login() view.
def _sync_session_on_login(sender, request, user, **kwargs):
	request.session['username'] = user.username
	request.session['superuser'] = user.is_superuser

user_logged_in.connect(_sync_session_on_login)

def _is_superuser(request):
	return bool(request.user.is_authenticated and request.session.get('superuser'))

def _session_user(request):
	if request.user.is_authenticated:
		return request.session.get('username', ''), request.session.get('superuser', '')
	return '', ''

QUESTION_TYPES = ['Continuous', 'Situational']

def _type_select(selected=''):
	options = format_html_join(
		'', '<option value="{}" {}>{}</option>',
		((t, 'selected' if t == selected else '', t) for t in QUESTION_TYPES),
	)
	return format_html('<select name="type" class="form-control">{}</select>', options)

def _category_select(selected='', qtype=None):
	qs = Questions.objects.all()
	if qtype:
		qs = qs.filter(questionType=qtype)
	categories = qs.values_list('questionCategory', flat=True).distinct().order_by('questionCategory')
	options = format_html_join(
		'', '<option value="{}" {}>{}</option>',
		((c, 'selected' if c == selected else '', c) for c in categories),
	)
	other_selected = 'selected' if selected and selected not in categories else ''
	return format_html(
		'<div id="c"><select id="cat" name="cat" class="form-control">{}<option value="Others" {}>Others (type a new category)</option></select></div>',
		options, other_selected,
	)

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

	return render(request, 'questions_fragment.html', {
		'questions': questions,
		'superuser': _is_superuser(request),
	})

def _redirect_to_browse(qtype):
	return HttpResponseRedirect('/continuous' if qtype == 'Continuous' else '/situational')

#Add Question page - superuser only
def add_question(request):
	usr, superuser = _session_user(request)
	if not superuser:
		return render(request, 'add_question.html', {'user': usr, 'superuser': superuser})

	default_type = request.GET.get('type', 'Continuous')
	if default_type.lower() == 'situational':
		default_type = 'Situational'

	return render(request, 'add_question.html', {
		'type': _type_select(default_type),
		'cat': _category_select(qtype=default_type),
		'sit': '',
		'themes': '',
		'user': usr,
		'superuser': superuser,
	})

#Handles the POST from add_question.html
def insert_question(request):
	usr, superuser = _session_user(request)
	if not superuser or request.method != 'POST':
		return HttpResponseRedirect('/403/')

	question_text = request.POST.get('question', '').strip()
	qtype = request.POST.get('type', '').strip()
	category = request.POST.get('cat', '').strip()
	answer_text = request.POST.get('answer', '').strip()

	errors = []
	if not question_text or question_text == 'Type your question here':
		errors.append('Question text is required.')
	if qtype not in QUESTION_TYPES:
		errors.append('Please choose a writing type.')
	if not category:
		errors.append('Category is required.')
	if not answer_text or answer_text == 'Type your answer here':
		errors.append('Model answer is required.')

	if errors:
		return render(request, 'add_question.html', {
			'errors': errors,
			'question': question_text,
			'answer': answer_text,
			'type': _type_select(qtype),
			'cat': _category_select(category, qtype=qtype or None),
			'sit': '',
			'themes': '',
			'user': usr,
			'superuser': superuser,
		})

	question = Questions.objects.create(
		questionid=_next_question_id(),
		question=question_text,
		questionCategory=category,
		questionType=qtype,
	)
	ModelAns.objects.create(ansid=_next_ans_id(), questionid=question, ans=answer_text)

	pic_file = request.FILES.get('pic')
	pic_warning = None
	if pic_file:
		try:
			ext = os.path.splitext(pic_file.name)[1]
			filename = f'{uuid.uuid4().hex}{ext}'
			dest_dir = os.path.join(settings.BASE_DIR, 'writingwiz', 'static', 'pictures')
			os.makedirs(dest_dir, exist_ok=True)
			with open(os.path.join(dest_dir, filename), 'wb') as f:
				for chunk in pic_file.chunks():
					f.write(chunk)
			Pictorial.objects.create(picid=_next_pic_id(), questionid=question, url=filename)
		except OSError:
			# Vercel's filesystem is read-only at runtime - there's nowhere to
			# persist an uploaded file without adding external object storage.
			# The question/answer are still saved; only the picture is skipped.
			pic_warning = (
				'The question and answer were saved, but the picture could not be uploaded - '
				'this deployment has no persistent file storage configured.'
			)

	if pic_warning:
		return render(request, 'add_question.html', {
			'errors': [pic_warning],
			'type': _type_select(),
			'cat': _category_select(),
			'sit': '',
			'themes': '',
			'user': usr,
			'superuser': superuser,
		})

	return _redirect_to_browse(qtype)

#Edit Question page - superuser only
def edit_question(request, question_id):
	usr, superuser = _session_user(request)
	if not superuser:
		return render(request, 'edit_question.html', {'user': usr, 'superuser': superuser})

	question = get_object_or_404(Questions, pk=question_id)
	pictures = question.pictorial_set.all()
	picture_block = format_html_join(
		'', '<p><img src="/static/pictures/{}" style="max-width:200px;"><br>{}</p>',
		((p.url, p.url) for p in pictures),
	) if pictures else format_html('<p class="text-muted">No picture uploaded for this question yet.</p>')

	return render(request, 'edit_question.html', {
		'qid': question.questionid,
		'question': question.question,
		'picture': picture_block,
		'type': _type_select(question.questionType),
		'cat': _category_select(question.questionCategory, qtype=question.questionType),
		'themes': '',
		'user': usr,
		'superuser': superuser,
	})

#Handles the POST from edit_question.html
def update_question(request):
	usr, superuser = _session_user(request)
	if not superuser or request.method != 'POST':
		return HttpResponseRedirect('/403/')

	question = get_object_or_404(Questions, pk=request.POST.get('qid'))
	question.question = request.POST.get('question', '').strip()
	question.questionType = request.POST.get('type', '').strip() or question.questionType
	question.questionCategory = request.POST.get('cat', '').strip() or question.questionCategory
	question.save()

	return _redirect_to_browse(question.questionType)

#Edit Answer page - superuser only
def edit_answer_view(request, ans_id):
	usr, superuser = _session_user(request)
	if not superuser:
		return render(request, 'edit_answer.html', {'user': usr, 'superuser': superuser})

	answer = get_object_or_404(ModelAns, pk=ans_id)
	return render(request, 'edit_answer.html', {
		'qid': answer.questionid_id,
		'aid': answer.ansid,
		'answer': answer.ans,
		'user': usr,
		'superuser': superuser,
	})

#Handles the POST from edit_answer.html
def update_answer(request):
	usr, superuser = _session_user(request)
	if not superuser or request.method != 'POST':
		return HttpResponseRedirect('/403/')

	answer = get_object_or_404(ModelAns, pk=request.POST.get('aid'))
	answer.ans = request.POST.get('answer', '').strip()
	answer.save()

	question = Questions.objects.filter(pk=request.POST.get('qid')).first()
	return _redirect_to_browse(question.questionType if question else 'Continuous')

