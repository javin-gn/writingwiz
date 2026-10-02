from django.http import Http404
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.db import connection
from django.db.models import Count, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.template import RequestContext
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash

import hashlib
from functools import wraps

from django.utils.html import format_html, format_html_join

from django.shortcuts import get_object_or_404
from django.contrib.auth.signals import user_logged_in

import os
import uuid

from django.conf import settings

from .models import (
	Greeting, Questions, ModelAns, Pictorial, LearningVideo, Vocabulary, Phrase,
	EssayAttempt, Announcement, SiteSettings, VividVocabularyUsage,
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

def login_required_view(view_func):
	"""Redirects to /login/ (returning here afterwards) for full pages under
	Browse/Resources. Not for AJAX-fragment endpoints - see questions_browse,
	which returns a fragment instead since a redirect would dump a full login
	page's HTML into the #questions div."""
	@wraps(view_func)
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return HttpResponseRedirect('/login/?url=' + request.path)
		return view_func(request, *args, **kwargs)
	return wrapper

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
	announcements = Announcement.objects.filter(is_active=True)
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
		return render(request, 'index.html', {'user': usr, 'superuser': superuser, 'announcements': announcements})
	else:
		return render(request, 'index.html', {'user': "", 'superuser': "", 'announcements': announcements})


#Register Page
def register(request):
	site_settings = SiteSettings.load()
	registration_enabled = site_settings.registration_enabled
	google_signin_enabled = site_settings.google_signin_enabled
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
		return render(request, 'register.html', {'user': usr, 'superuser': superuser, 'registration_enabled': registration_enabled, 'google_signin_enabled': google_signin_enabled})
	else:
		return render(request, 'register.html', {'user': "", 'superuser': "", 'registration_enabled': registration_enabled, 'google_signin_enabled': google_signin_enabled})

#Login Page
def login(request):
	site_settings = SiteSettings.load()
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
		return render(request, 'login.html', {'user': usr, 'superuser': superuser})

	# Empty (not '/') when the login page was reached directly rather than
	# via a redirect from a protected page - lets a successful login below
	# fall through to the role-based dashboard instead of forcing '/'.
	next_url = request.GET.get('url') or ''
	errors = []
	username = ''

	if request.GET.get('google_disabled'):
		errors.append('Google Sign-In is currently disabled.')

	if request.method == 'POST':
		username = request.POST.get('username', '')
		password = request.POST.get('password', '')

		user = authenticate(request, username=username, password=password)
		if user is not None:
			auth_login(request, user)
			request.session['username'] = user.username
			request.session['superuser'] = user.is_superuser
			if next_url:
				redirect_to = next_url
			elif user.is_superuser:
				redirect_to = '/manage/'
			else:
				redirect_to = '/dashboard/'
			return HttpResponseRedirect(redirect_to)
		elif User.objects.filter(username=username, is_active=False).exists():
			errors.append('This account has been deactivated.')
		else:
			errors.append('Incorrect email or password.')

	return render(request, 'login.html', {
		'errors': errors,
		'username': username,
		'next': next_url,
		'google_signin_enabled': site_settings.google_signin_enabled,
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
		if not SiteSettings.load().registration_enabled:
			return render(request, 'register.html', {
				'errors': ['Registration is currently closed.'],
				'user': '', 'superuser': '', 'registration_enabled': False,
			})
		first_name = request.POST.get('first_name', '').strip()
		last_name = request.POST.get('last_name', '').strip()
		if not first_name:
			errors.append('First name is empty.')
		if not last_name:
			errors.append('Last name is empty.')
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
			user.first_name = first_name
			user.last_name = last_name
			user.is_active = True
			user.save()
			auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
			return HttpResponseRedirect('/dashboard/')
		else:
			return render(request, 'register.html', {
				'errors': errors,
				'first_name': first_name,
				'last_name': last_name,
				'username': request.POST['username'],
				'password': request.POST['password'],
				'cfmpassword': request.POST['cfmpassword'],
				'user': "", 'superuser': "", 'registration_enabled': True,
				'google_signin_enabled': SiteSettings.load().google_signin_enabled,
			})
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
		.values('questionCategory')
		.annotate(count=Count('questionid'))
		.order_by('questionCategory')
	)
	return format_html(
		'<ul class="list-unstyled category-list">{}</ul>',
		format_html_join(
			'',
			'<li><a href="#" class="category-link" onclick="loadQuestions(this, \'{}\', \'{}\'); return false;">{} <span class="category-count">{}</span></a></li>',
			((c['questionCategory'], qtype, c['questionCategory'], c['count']) for c in categories),
		),
	)

def _theme_link_list(qtype):
	themes = (
		Questions.objects.filter(questionType=qtype)
		.exclude(theme='')
		.values('theme')
		.annotate(count=Count('questionid'))
		.order_by('theme')
	)
	return format_html(
		'<ul class="list-unstyled category-list">{}</ul>',
		format_html_join(
			'',
			'<li><a href="#" class="category-link" onclick="loadQuestionsByTheme(this, \'{}\', \'{}\'); return false;">{} <span class="category-count">{}</span></a></li>',
			((t['theme'], qtype, t['theme'], t['count']) for t in themes),
		),
	)


#Continuous Writing browse page
@login_required_view
def continuous(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	return render(request, 'continuous.html', {
		'catlist': _category_link_list('Continuous'),
		'themelist': _theme_link_list('Continuous'),
		'addQuestionBtn': '',
		'content': '<div id="questions"><p>Select a category on the left to browse questions.</p></div>',
		'user': usr,
		'superuser': superuser,
	})

#Situational Writing browse page
@login_required_view
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
@login_required_view
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
@login_required_view
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
@login_required_view
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
@login_required_view
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

#Vivid Vocabulary Leaderboard - ranks students by distinct vivid vocabulary/
#phrase bank entries detected in their graded essays, per category
@login_required_view
def leaderboard(request):
	usr, superuser = _session_user(request)

	rankings = (
		VividVocabularyUsage.objects.values('user_id', 'user__first_name', 'user__last_name', 'user__username')
		.annotate(count=Count('id'))
		.order_by('-count')[:50]
	)

	return render(request, 'leaderboard.html', {
		'user': usr,
		'superuser': superuser,
		'rankings': rankings,
		'current_user_id': request.user.id,
	})

_THEME_FILLER_WORDS = {'and', '&', 'the', 'of'}

def _theme_words(theme):
	return {w for w in theme.lower().replace('&', ' ').split() if w not in _THEME_FILLER_WORDS}

def _vivid_vocabulary_for_theme(theme, limit=12):
	"""Vocabulary/Phrase 'theme' values use the same theme names as Questions,
	but entered inconsistently ("Outdoor" vs "Outdoor Activities", "Accidents &
	Disasters" vs "Accidents and Disasters") - there's no field that survives an
	exact match, so this matches on word overlap instead. There is no similar
	link for *category* - Vocabulary/Phrase categories are word-topic groups
	(Emotions, Actions & Movements) while Questions categories are writing
	formats (Letter, Picture-Based); the two taxonomies don't correspond at all,
	so no suggestion can honestly be made from category.
	"""
	if not theme:
		return []
	target_words = _theme_words(theme)
	if not target_words:
		return []

	suggestions = []
	for word, entry_theme in Vocabulary.objects.exclude(theme='').values_list('vocabulary', 'theme'):
		if _theme_words(entry_theme) & target_words:
			suggestions.append(word.strip())
	for phrase, entry_theme in Phrase.objects.exclude(theme='').values_list('phrase', 'theme'):
		if _theme_words(entry_theme) & target_words:
			suggestions.append(phrase.strip())
	return suggestions[:limit]

#Standalone rule-based PSLE essay grader - not an AI/LLM assessment, see grading.py
@login_required_view
def essay_grader(request):
	if request.user.is_authenticated:
		usr = request.session.get("username", "")
		superuser = request.session.get("superuser", "")
	else:
		usr = ""
		superuser = ""

	result = None
	essay_text = ''

	if request.method == 'POST':
		essay_text = request.POST.get('essay', '')
		qtype = request.POST.get('qtype', 'Continuous')
		question_id = request.POST.get('question_id', '')

		question = Questions.objects.filter(questionid=question_id).first() if question_id else None
		question_text = question.question if question else ''
		if question:
			qtype = question.questionType

		result = grade_essay(essay_text, qtype=qtype, question_text=question_text)

		attempt = EssayAttempt.objects.create(
			user=request.user,
			question=question,
			qtype=qtype,
			essay_text=essay_text,
			total_score=result['total_score'],
			total_max=result['total_max'],
			content_score=result['content_score'],
			content_max=result['content_max'],
			language_score=result['language_score'],
			language_max=result['language_max'],
			breakdown=result['breakdown'],
			suggestions=result['suggestions'],
		)
		VividVocabularyUsage.objects.bulk_create([
			VividVocabularyUsage(
				user=request.user,
				attempt=attempt,
				kind=hit['kind'],
				text=hit['text'],
				category=hit['category'],
			)
			for hit in result['vivid_hits']
		])
	else:
		qtype = request.GET.get('qtype', 'Continuous')
		if qtype not in QUESTION_TYPES:
			qtype = 'Continuous'
		question = None
		requested_qid = request.GET.get('question_id')
		if requested_qid:
			question = Questions.objects.filter(questionid=requested_qid).first()
			if question:
				qtype = question.questionType
		if question is None:
			# order_by('?') -> a fresh random question each load/refresh, for both sqlite and postgres
			question = Questions.objects.filter(questionType=qtype).order_by('?').first()
		question_id = question.questionid if question else ''

	vocab_suggestions = _vivid_vocabulary_for_theme(question.theme if question else '')
	attempt_history = (
		EssayAttempt.objects.filter(user=request.user, question=question)
		if question else EssayAttempt.objects.none()
	)

	return render(request, 'essay_grader.html', {
		'question': question,
		'essay_text': essay_text,
		'qtype': qtype,
		'question_id': question_id,
		'vocab_suggestions': vocab_suggestions,
		'attempt_history': attempt_history,
		'user': usr,
		'superuser': superuser,
	})

#Profile page - user details, password change, and overall essay grading stats
@login_required_view
def profile(request):
	user = request.user
	errors = []
	success = None

	if request.method == 'POST':
		action = request.POST.get('action')

		if action == 'update_details':
			new_email = request.POST.get('email', '').strip()
			new_first_name = request.POST.get('first_name', '').strip()
			new_last_name = request.POST.get('last_name', '').strip()
			if not new_first_name:
				errors.append('First name cannot be empty.')
			elif not new_last_name:
				errors.append('Last name cannot be empty.')
			elif not new_email or '@' not in new_email:
				errors.append('Please enter a valid email address.')
			elif User.objects.filter(username=new_email).exclude(pk=user.pk).exists():
				errors.append('That email is already in use.')
			else:
				user.email = new_email
				user.username = new_email
				user.first_name = new_first_name
				user.last_name = new_last_name
				user.save()
				request.session['username'] = user.username
				success = 'Your details have been updated.'

		elif action == 'change_password':
			current_password = request.POST.get('current_password', '')
			new_password = request.POST.get('new_password', '')
			confirm_password = request.POST.get('confirm_password', '')
			if not user.check_password(current_password):
				errors.append('Current password is incorrect.')
			elif not new_password:
				errors.append('New password cannot be empty.')
			elif new_password != confirm_password:
				errors.append('New passwords do not match.')
			else:
				user.set_password(new_password)
				user.save()
				update_session_auth_hash(request, user)  # keep the user logged in
				success = 'Your password has been updated.'

	usr, superuser = _session_user(request)
	return render(request, 'profile.html', {
		'errors': errors,
		'success': success,
		'email': user.email,
		'first_name': user.first_name,
		'last_name': user.last_name,
		'date_joined': user.date_joined,
		'user': usr,
		'superuser': superuser,
	})

#Student dashboard - progress and score overview, landing page after a non-admin login
@login_required_view
def dashboard(request):
	user = request.user
	attempts = EssayAttempt.objects.filter(user=user)
	total_attempts = attempts.count()

	avg_percent = None
	best_percent = None
	avg_content_percent = None
	avg_language_percent = None
	continuous_avg = None
	situational_avg = None

	if total_attempts:
		percents = [a.percent for a in attempts]
		avg_percent = round(sum(percents) / len(percents))
		best_percent = max(percents)

		content_percents = [a.content_percent for a in attempts if a.content_max]
		language_percents = [a.language_percent for a in attempts if a.language_max]
		if content_percents:
			avg_content_percent = round(sum(content_percents) / len(content_percents))
		if language_percents:
			avg_language_percent = round(sum(language_percents) / len(language_percents))

		continuous_percents = [a.percent for a in attempts if a.qtype == 'Continuous']
		situational_percents = [a.percent for a in attempts if a.qtype == 'Situational']
		if continuous_percents:
			continuous_avg = round(sum(continuous_percents) / len(continuous_percents))
		if situational_percents:
			situational_avg = round(sum(situational_percents) / len(situational_percents))

	vivid_usage = VividVocabularyUsage.objects.filter(user=user)
	vivid_total = vivid_usage.values('text').distinct().count()
	# Dedup in Python rather than .distinct() - a DISTINCT + ORDER BY on a
	# column outside the SELECT list (created_at isn't selected here) is
	# rejected by Postgres even though sqlite tolerates it.
	vivid_recent_words = []
	for text in vivid_usage.order_by('-created_at').values_list('text', flat=True)[:200]:
		if text not in vivid_recent_words:
			vivid_recent_words.append(text)
		if len(vivid_recent_words) >= 10:
			break

	usr, superuser = _session_user(request)
	return render(request, 'dashboard.html', {
		'total_attempts': total_attempts,
		'avg_percent': avg_percent,
		'best_percent': best_percent,
		'avg_content_percent': avg_content_percent,
		'avg_language_percent': avg_language_percent,
		'continuous_avg': continuous_avg,
		'situational_avg': situational_avg,
		'recent_attempts': attempts[:15],
		'vivid_total': vivid_total,
		'vivid_recent_words': vivid_recent_words,
		'user': usr,
		'superuser': superuser,
	})

#AJAX endpoint used by continuous.html / situational.html to load a filtered question list
def questions_browse(request):
	if not request.user.is_authenticated:
		return HttpResponse('<p>Please <a href="/login/?url=/continuous">log in</a> to view questions.</p>')

	qtype = request.GET.get('type', '')
	category = request.GET.get('query', '')
	theme = request.GET.get('theme', '')

	questions = Questions.objects.filter(questionType=qtype)
	if category:
		questions = questions.filter(questionCategory=category)
	if theme:
		questions = questions.filter(theme=theme)
	# Without this, questions_fragment.html's per-question pictorial_set.all /
	# modelans_set.all / essay_attempts.all loops each fire their own query -
	# prefetch collapses that N+1 into a handful of queries total, which
	# matters a lot once DATABASE_URL points at a remote Postgres instance
	# instead of local sqlite.
	questions = questions.order_by('questionid').prefetch_related(
		'pictorial_set', 'modelans_set',
		Prefetch('essay_attempts', queryset=EssayAttempt.objects.select_related('user')),
	)

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

