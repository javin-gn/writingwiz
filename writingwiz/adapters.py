from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import SiteSettings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return SiteSettings.load().registration_enabled


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        # Only gates brand-new accounts - an existing linked Google account
        # logging back in is a login, not a signup, and isn't affected.
        return SiteSettings.load().registration_enabled
