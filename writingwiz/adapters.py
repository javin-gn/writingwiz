from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseRedirect

from .models import SiteSettings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return SiteSettings.load().registration_enabled

    def get_login_redirect_url(self, request):
        # Only consulted when no explicit ?next= was passed through the
        # Google login link - an explicit next (e.g. a page that redirected
        # here to log in) always wins, same as the plain email/password login.
        if request.user.is_superuser:
            return '/manage/'
        return '/dashboard/'

    def get_signup_redirect_url(self, request):
        # New accounts via Google are never superusers.
        return '/dashboard/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Runs before every Google login attempt, new account or returning
        # user alike - the master "Google Sign-In" switch, separate from
        # is_open_for_signup below which only gates new-account creation.
        if not SiteSettings.load().google_signin_enabled:
            raise ImmediateHttpResponse(HttpResponseRedirect('/login/?url=/&google_disabled=1'))
        super().pre_social_login(request, sociallogin)

    def is_open_for_signup(self, request, sociallogin):
        # Only gates brand-new accounts - an existing linked Google account
        # logging back in is a login, not a signup, and isn't affected.
        return SiteSettings.load().registration_enabled
