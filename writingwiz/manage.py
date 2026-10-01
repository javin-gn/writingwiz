"""Custom admin module - replaces django.contrib.admin, which this project no
longer uses. Each view here is gated to superusers only, following the same
convention as add_question/edit_question in views.py: a non-superuser GET
sees an inline "not allowed" message, a non-superuser POST is redirected to
/403/.
"""

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .models import Announcement, Vocabulary, Phrase, LearningVideo, EssayAttempt, Questions, SiteSettings
from .views import _session_user, QUESTION_TYPES


def _superuser_guard(request, usr, superuser, template_name):
    if superuser:
        return None
    if request.method == 'POST':
        return HttpResponseRedirect('/403/')
    return render(request, template_name, {'user': usr, 'superuser': superuser})


def _paginate(request, queryset, param='page', per_page=25):
    """Paginates queryset and builds prev/next URLs that preserve every other
    query-string param (filters, ?edit=, a second list's own page param on a
    page with two paginated tables, etc) - only `param` itself is replaced."""
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get(param))

    base = request.GET.copy()
    prev_url = None
    if page_obj.has_previous():
        base[param] = page_obj.previous_page_number()
        prev_url = '?' + base.urlencode()
    next_url = None
    if page_obj.has_next():
        base[param] = page_obj.next_page_number()
        next_url = '?' + base.urlencode()

    return page_obj, prev_url, next_url


def dashboard(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_dashboard.html')
    if guard:
        return guard

    return render(request, 'manage_dashboard.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'dashboard',
        'question_count': Questions.objects.count(),
        'announcement_count': Announcement.objects.count(),
        'account_count': User.objects.count(),
        'vocabulary_count': Vocabulary.objects.count(),
        'phrase_count': Phrase.objects.count(),
        'video_count': LearningVideo.objects.count(),
        'essay_count': EssayAttempt.objects.count(),
    })


def announcements(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_announcements.html')
    if guard:
        return guard

    errors = []
    success = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            pk = request.POST.get('pk')
            title = request.POST.get('title', '').strip()
            message = request.POST.get('message', '').strip()
            level = request.POST.get('level', 'info')
            is_active = bool(request.POST.get('is_active'))

            if not title or not message:
                errors.append('Title and message are required.')
            elif pk:
                ann = Announcement.objects.filter(pk=pk).first()
                if ann:
                    ann.title = title
                    ann.message = message
                    ann.level = level
                    ann.is_active = is_active
                    ann.save()
                    success = 'Announcement updated.'
                else:
                    errors.append('Announcement not found.')
            else:
                Announcement.objects.create(title=title, message=message, level=level, is_active=is_active)
                success = 'Announcement added.'

        elif action == 'toggle':
            ann = Announcement.objects.filter(pk=request.POST.get('pk')).first()
            if ann:
                ann.is_active = not ann.is_active
                ann.save()
                success = f'"{ann.title}" is now {"active" if ann.is_active else "inactive"}.'

        elif action == 'delete':
            ann = Announcement.objects.filter(pk=request.POST.get('pk')).first()
            if ann:
                ann.delete()
                success = 'Announcement deleted.'

    editing = None
    edit_id = request.GET.get('edit')
    if edit_id:
        editing = Announcement.objects.filter(pk=edit_id).first()
        if not editing:
            errors.append('That announcement no longer exists.')

    page_obj, prev_url, next_url = _paginate(request, Announcement.objects.all(), per_page=15)

    return render(request, 'manage_announcements.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'announcements',
        'errors': errors,
        'success': success,
        'announcements': page_obj,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
        'editing': editing,
    })


def accounts(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_accounts.html')
    if guard:
        return guard

    errors = []
    success = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_registration':
            site_settings = SiteSettings.load()
            site_settings.registration_enabled = not site_settings.registration_enabled
            site_settings.save()
            success = f'Registration is now {"open" if site_settings.registration_enabled else "closed"}.'
        elif action == 'toggle_google_signin':
            site_settings = SiteSettings.load()
            site_settings.google_signin_enabled = not site_settings.google_signin_enabled
            site_settings.save()
            success = f'Google Sign-In is now {"enabled" if site_settings.google_signin_enabled else "disabled"}.'
        else:
            target = User.objects.filter(pk=request.POST.get('pk')).first()

            if not target:
                errors.append('Account not found.')
            elif target.pk == request.user.pk:
                errors.append('You cannot change your own account status here.')
            elif action == 'toggle_active':
                target.is_active = not target.is_active
                target.save()
                success = f'{target.username} is now {"active" if target.is_active else "inactive"}.'
            elif action == 'toggle_admin':
                target.is_superuser = not target.is_superuser
                target.save()
                success = f'{target.username} is now {"an admin" if target.is_superuser else "a regular user"}.'

    accounts_qs = User.objects.annotate(essay_count=Count('essay_attempts')).order_by('-date_joined')
    page_obj, prev_url, next_url = _paginate(request, accounts_qs, per_page=25)

    return render(request, 'manage_accounts.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'accounts',
        'errors': errors,
        'success': success,
        'accounts': page_obj,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
        'user_pk': request.user.pk,
        'registration_enabled': SiteSettings.load().registration_enabled,
        'google_signin_enabled': SiteSettings.load().google_signin_enabled,
    })


def vocabulary(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_vocabulary.html')
    if guard:
        return guard

    errors = []
    success = None

    if request.method == 'POST':
        kind = request.POST.get('kind')
        model = {'vocabulary': Vocabulary, 'phrase': Phrase}.get(kind)
        field = kind
        action = request.POST.get('action')

        if model is None:
            errors.append('Invalid request.')
        elif action == 'add':
            text = request.POST.get('text', '').strip()
            category = request.POST.get('category', '').strip()
            theme = request.POST.get('theme', '').strip()
            if not text or not category:
                errors.append('Word/phrase and category are required.')
            elif model.objects.filter(pk=text).exists():
                errors.append(f'"{text}" already exists.')
            else:
                model.objects.create(**{field: text, 'category': category, 'theme': theme})
                success = f'Added "{text}".'

        elif action == 'update':
            obj = model.objects.filter(pk=request.POST.get('pk')).first()
            category = request.POST.get('category', '').strip()
            if not obj:
                errors.append('Not found.')
            elif not category:
                errors.append('Category is required.')
            else:
                obj.category = category
                obj.theme = request.POST.get('theme', '').strip()
                obj.save()
                success = f'Updated "{obj.pk}".'

        elif action == 'delete':
            obj = model.objects.filter(pk=request.POST.get('pk')).first()
            if obj:
                obj.delete()
                success = 'Deleted.'

    vocab_page, vocab_prev_url, vocab_next_url = _paginate(
        request, Vocabulary.objects.all().order_by('vocabulary'), param='vocab_page', per_page=25)
    phrase_page, phrase_prev_url, phrase_next_url = _paginate(
        request, Phrase.objects.all().order_by('phrase'), param='phrase_page', per_page=25)

    return render(request, 'manage_vocabulary.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'vocabulary',
        'errors': errors,
        'success': success,
        'vocab_list': vocab_page,
        'vocab_page_obj': vocab_page,
        'vocab_prev_url': vocab_prev_url,
        'vocab_next_url': vocab_next_url,
        'phrase_list': phrase_page,
        'phrase_page_obj': phrase_page,
        'phrase_prev_url': phrase_prev_url,
        'phrase_next_url': phrase_next_url,
    })


def videos(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_videos.html')
    if guard:
        return guard

    errors = []
    success = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            pk = request.POST.get('pk')
            title = request.POST.get('title', '').strip()
            url = request.POST.get('url', '').strip()

            if not title or not url:
                errors.append('Title and URL are required.')
            elif pk:
                video = LearningVideo.objects.filter(pk=pk).first()
                if video:
                    video.title = title
                    video.url = url
                    video.save()
                    success = 'Video updated.'
                else:
                    errors.append('Video not found.')
            else:
                LearningVideo.objects.create(title=title, url=url)
                success = 'Video added.'

        elif action == 'delete':
            video = LearningVideo.objects.filter(pk=request.POST.get('pk')).first()
            if video:
                video.delete()
                success = 'Video deleted.'

    editing = None
    edit_id = request.GET.get('edit')
    if edit_id:
        editing = LearningVideo.objects.filter(pk=edit_id).first()
        if not editing:
            errors.append('That video no longer exists.')

    page_obj, prev_url, next_url = _paginate(request, LearningVideo.objects.all().order_by('-dateCreated'), per_page=15)

    return render(request, 'manage_videos.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'videos',
        'errors': errors,
        'success': success,
        'videos': page_obj,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
        'editing': editing,
    })


def essays(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_essays.html')
    if guard:
        return guard

    success = None

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        attempt = EssayAttempt.objects.filter(pk=request.POST.get('pk')).first()
        if attempt:
            attempt.delete()
            success = 'Attempt deleted.'

    attempts_qs = EssayAttempt.objects.select_related('user', 'question').order_by('-created_at')
    page_obj, prev_url, next_url = _paginate(request, attempts_qs, per_page=25)

    return render(request, 'manage_essays.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'essays',
        'success': success,
        'attempts': page_obj,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
        'total_count': EssayAttempt.objects.count(),
    })


def questions(request):
    usr, superuser = _session_user(request)
    guard = _superuser_guard(request, usr, superuser, 'manage_questions.html')
    if guard:
        return guard

    success = None

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        q = Questions.objects.filter(pk=request.POST.get('pk')).first()
        if q:
            q.delete()
            success = f'Question #{q.questionid} deleted.'

    qtype_filter = request.GET.get('type', '')
    qs = Questions.objects.all().order_by('questionid')
    if qtype_filter in QUESTION_TYPES:
        qs = qs.filter(questionType=qtype_filter)
    qs = qs.prefetch_related('modelans_set', 'pictorial_set')

    page_obj, prev_url, next_url = _paginate(request, qs, per_page=20)

    return render(request, 'manage_questions.html', {
        'user': usr,
        'superuser': superuser,
        'active': 'questions',
        'success': success,
        'questions': page_obj,
        'page_obj': page_obj,
        'prev_url': prev_url,
        'next_url': next_url,
        'qtype_filter': qtype_filter,
        'continuous_count': Questions.objects.filter(questionType='Continuous').count(),
        'situational_count': Questions.objects.filter(questionType='Situational').count(),
    })
