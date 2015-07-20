from django.conf import settings
from login.models import Users
from .facebook_request import GraphAPIRequest
from .facebook_helper import GraphAPIHelper
from urllib import urlencode
import tasks


class FacebookLoginHandler(object):

    def __init__(self, request):
        self._request = request
        self._user_data = {}

    @property
    def user_data(self):
        return self._user_data

    def is_login(self):
        if self._login_with_session():
            return True
        if self._login_from_facebook_redirect():
            return True
        return False

    def _login_with_session(self):
        fb_id = self._request.session.get('fb_id', None)
        access_token = self._request.session.get('access_token', None)
        user = self.get_user(fb_id)
        if fb_id and access_token and user:
            self._user_data = user
            return GraphAPIHelper.validate_access_token(access_token)
        return False

    def _login_from_facebook_redirect(self):
        if 'code' in self._request.GET:
            code = self._request.GET['code']
            res = self.get_access_token_from_code(code)
            if 'error' not in res and 'access_token' in res:
                access_token = res['access_token']
                res['user_data'] = GraphAPIRequest(
                    access_token, '/me').get().response
                fb_id = res['user_data']['id']

                self._set_login_session(res)
                user = self.get_user(fb_id)
                if not user:
                    self.on_new_user(res)
                    user = self.get_user(fb_id)
                self._user_data = user
                return True
        return False

    def on_new_user(self, data):
        self._register_tasks(data)
        self._create_user(data)

    def _create_user(self, data):
        fb_id = data['user_data']['id']
        user_data = data['user_data']
        del user_data['id']

        Users.objects.create(
            fb_id=fb_id,
            access_token=data.get('access_token', None),
            access_token_expires=data.get('expires', 0),
            **user_data
        )

    def get_user(self, fb_id):
        user = Users.objects.filter(fb_id=fb_id).first()
        if user:
            return user
        return False

    def _register_tasks(self, data):
        tasks.fetch_all(data['user_data']['id'])

    def _set_login_session(self, res):
        self._request.session['fb_id'] = res['user_data']['id']
        self._request.session['access_token'] = res['access_token']

    @staticmethod
    def get_access_token_from_code(code, redirect_uri=settings.URL_SITE,
                                   app_id=settings.FACEBOOK_APP_ID,
                                   app_secret=settings.FACEBOOK_SECRET):
        args = {
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": app_id,
            "client_secret": app_secret}

        return GraphAPIRequest(None, "oauth/access_token", args).get().response

    @staticmethod
    def get_login_url():
        url = "https://www.facebook.com/dialog/oauth?"
        kvps = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': settings.URL_SITE,
        }
        kvps['scope'] = ",".join(settings.SCOPE_PREMISSON)

        return url + urlencode(kvps)
