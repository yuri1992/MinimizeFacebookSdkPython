from django.test import TestCase
from django.conf import settings
from .facebook_request import GraphReponse, GraphAPIError, GraphAPIRequest
from .facebook_login import FacebookLoginHandler
from login.models import Users
from mongoengine import connect


class MockGraphResponse(object):

    def __init__(self, d):
        self.__dict__.update(d)

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def json(self):
        return self.__dict__['response']


class TestGraphResponse(TestCase):

    def setUp(self):
        pass

    def test_json_response(self):
        mock = MockGraphResponse({
            'headers': {
                'content-type': 'application/json; charset=UTF-8'
            },
            'response': {
                'bla': 'bla'
            }
        })
        res = GraphReponse(mock)
        self.assertDictEqual({'bla': 'bla'}, res.response)

        self.assertFalse(res.next_page)
        self.assertFalse(res.previous_page)

    def test_image_response(self):
        mock = MockGraphResponse({
            'headers': {
                'content-type': 'image/jpeg/isdsf'
            },
            'response': {

            },
            'content': {
                'bla': 'asdasdasd'
            },
            'url': 'http://check.com'
        })
        res = GraphReponse(mock)

        self.assertDictEqual({
            'mime-type': 'image/jpeg/isdsf',
            'data': {
                'bla': 'asdasdasd'
            },
            'url': 'http://check.com'
        }, res.response)

        self.assertFalse(res.next_page)
        self.assertFalse(res.previous_page)

    def test_access_token_response(self):
        mock = MockGraphResponse({
            'headers': {
                'content-type': 'html/text'
            },
            'text': "access_token=test_arg&expires=123",
        })
        res = GraphReponse(mock)
        self.assertDictEqual({
            'access_token': 'test_arg',
            'expires': '123',
        }, res.response)
        self.assertFalse(res.next_page)
        self.assertFalse(res.previous_page)

        mock = MockGraphResponse({
            'headers': {
                'content-type': 'html/text'
            },
            'text': "no_token=test_arg&expires=123",
        })
        self.assertRaises(GraphAPIError, lambda: GraphReponse(mock))

    def test_paging(self):
        mock = MockGraphResponse({
            'headers': {
                'content-type': 'application/json; charset=UTF-8'
            },
            'response': {
                'paging': {
                    'next': 'link'
                }
            }
        })
        res = GraphReponse(mock)

        self.assertTrue(res.next_page)
        self.assertEqual('link', res.next_page)
        self.assertFalse(res.previous_page)

        mock = MockGraphResponse({
            'headers': {
                'content-type': 'application/json; charset=UTF-8'
            },
            'response': {
                'paging': {
                    'previous': 'link'
                }
            }
        })
        res = GraphReponse(mock)
        self.assertFalse(res.next_page)
        self.assertTrue(res.previous_page)
        self.assertEqual('link', res.previous_page)

    


class TestRequestGraph(TestCase):

    def setUp(self):
        self.req = GraphAPIRequest(
            "access_token",
            "/me",
            {}
        )

    def test_initial_request_obj(self):
        self.assertEqual("access_token", self.req.access_token)
        self.assertEqual("/me", self.req.path)
        self.assertEqual({}, self.req.args)
        self.assertEqual({}, self.req.response)

    def test_get_request_no_access(self):
        res = self.req.get()
        self.assertEqual(
            {u'error': {u'message': u'Invalid OAuth access token.',
                        u'code': 190, u'type': u'OAuthException'}},
            res.response
        )
        self.assertFalse(res.previous_page)
        self.assertFalse(res.next_page)

    def test_get_request_erroring(self):
        args = {
            'code': '123123123'
        }
        res = GraphAPIRequest(None,
                              "oauth/access_token",
                              args).get().response
        self.assertEqual(
            {u'error': {u'message': u'Missing redirect_uri parameter.',
                        u'code': 191, u'type': u'OAuthException'}},
            res
        )
        args = {
            'code': '123123123',
            'redirect_uri': settings.URL_SITE
        }
        res = GraphAPIRequest(None,
                              "oauth/access_token",
                              args).get().response
        self.assertEqual(
            {u'error': {u'message': u'Missing client_id parameter.',
                        u'code': 101, u'type': u'OAuthException'}},
            res
        )


class TestLoginHandler(TestCase):

    def setUp(self):
        self.login = FacebookLoginHandler({})

    def test_auth_url(self):
        url = self.login.get_login_url()
        self.assertEqual(
            "https://www.facebook.com/dialog/oauth?scope=user_likes%2Cuser_photos%2Cuser_status%2Cuser_videos%2Cuser_posts%2Cpublish_actions&redirect_uri=http%3A%2F%2Flocal.ynet.co.il%3A8080%2Flogin%2F&client_id=1649266495305734", url)

    def test_access_token_from_code(self):
        access_token = self.login.get_access_token_from_code(0)
        self.assertDictEqual(
            {
                u'error': {
                    u'message': u'Invalid verification code format.',
                    u'code': 100, u'type': u'OAuthException'}
            },
            access_token)

        access_token = self.login.get_access_token_from_code(
            r"AQABWZpImDWkZbshde6arYqyHHkIyOgQfSPVtC67m_ZR6Yr0xEYO5Uuws-gYjxOHAcZzocvooxF2jzadmy4OlUjp-qOIbI1X7yfxy6DDfrDx-b-1xTAGiV6unptZ4CTLThF9PCa1sel0UnegP0dpmUTnLLC10DZ7eD02xAhQy6yMd8erFB_Uf10DAbqVZDXANU72IqNnNrl8O-A1RVLyzcKW_hwo-lMk5824sFobZTCDnT3U2L1-BNjL7nwZQth15SQdaFfJ3RsP0DVhClxaRbymG2gCQRAudUVDgNkeA2UJUD9Hrqf30MIs2NAK9A1vkAI#_=_")
        self.assertEqual(
            {
                u'error': {u'message': u'This authorization code has expired.',
                           u'code': 100, u'type': u'OAuthException'}
            },
            access_token)

    def test_on_new_user(self):

        connect('test', host='mongodb://localhost/test')
        user_obj = {
            'user_data': {
                'id': 123123123,
                'name': 'Unit Test',
                'email': 'unit@test.com',
            },
            'access_token': 'unittest',
            'expires':  12312
        }
        self.assertEqual('unittest', user_obj.get('access_token', None))
        self.login.on_new_user(user_obj)
