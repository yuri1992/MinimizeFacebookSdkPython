from .facebook_request import GraphAPIRequest
from django.conf import settings


class GraphAPIHelper(object):

    @classmethod
    def get_connections(cls, id, connection_name, **args):
        """Fetchs the connections for given object."""
        return self.request(
            settings.FACEBOOK_VERSION + "/" + id + "/" + connection_name, args)

    def put_object(self, parent_object, connection_name, **data):
        """Writes the given object to the graph, connected to the given parent.

        For example,

            graph.put_object("me", "feed", message="Hello, world")

        writes "Hello, world" to the active user's wall. Likewise, this
        will comment on a the first post of the active user's feed:

            feed = graph.get_connections("me", "feed")
            post = feed["data"][0]
            graph.put_object(post["id"], "comments", message="First!")

        See http://developers.facebook.com/docs/api#publishing for all
        of the supported writeable objects.

        Certain write operations require extended permissions. For
        example, publishing to a user's feed requires the
        "publish_actions" permission. See
        http://developers.facebook.com/docs/publishing/ for details
        about publishing permissions.

        """
        assert self.access_token, "Write operations require an access token"
        return self.request(
            self.version + "/" + parent_object + "/" + connection_name,
            post_args=data,
            method="POST")

    def put_wall_post(self, message, attachment={}, profile_id="me"):
        """Writes a wall post to the given profile's wall.

        We default to writing to the authenticated user's wall if no
        profile_id is specified.

        attachment adds a structured attachment to the status message
        being posted to the Wall. It should be a dictionary of the form:

            {"name": "Link name"
             "link": "http://www.example.com/",
             "caption": "{*actor*} posted a new review",
             "description": "This is a longer description of the attachment",
             "picture": "http://www.example.com/thumbnail.jpg"}

        """
        return self.put_object(profile_id, "feed", message=message,
                               **attachment)

    def put_comment(self, object_id, message):
        """Writes the given comment on the given post."""
        return self.put_object(object_id, "comments", message=message)

    def put_like(self, object_id):
        """Likes the given post."""
        return self.put_object(object_id, "likes")

    def delete_object(self, id):
        """Deletes the object with the given ID from the graph."""
        self.request(self.version + "/" + id, method="DELETE")

    def delete_request(self, user_id, request_id):
        """Deletes the Request with the given ID for the given user."""
        self.request("%s_%s" % (request_id, user_id), method="DELETE")

    def put_photo(self, image, album_path="me/photos", **kwargs):
        """
        Upload an image using multipart/form-data.

        image - A file object representing the image to be uploaded.
        album_path - A path representing where the image should be uploaded.

        """
        return self.request(
            self.version + "/" + album_path,
            post_args=kwargs,
            files={"source": image},
            method="POST")

    def extend_access_token(self, access_token, app_id, app_secret):
        """
            Extends the expiration time of a valid OAuth access token. See
            <https://developers.facebook.com/roadmap/offline-access-removal/
            # extend_token>
        """
        args = {
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "fb_exchange_token",
            "fb_exchange_token": access_token,
        }
        return GraphAPIRequest(None,
                               "oauth/access_token",
                               args=args).get().response

    @classmethod
    def validate_access_token(cls, access_token):
        """
            Validate access token with Graph API
        """
        params = {
            'input_token': access_token
        }

        res = GraphAPIRequest(
            access_token,
            '/debug_token',
            params).get()

        if 'is_valid' in res.response['data']:
            return bool(res.response['data']['is_valid'])
        return False

    @staticmethod
    def get_user_photos(fb_id, access_token):
        """
            return all user photos by access_token
        """
        args = {
            'fields': 'likes.summary(true){pic_small,name,id,can_post},picture,name',
            'limit': '500'
        }
        res = GraphAPIRequest(access_token, '/me/photos', args).get_all()
        return res

    @staticmethod
    def get_user_videos(fb_id, access_token):
        """
            return all user photos by access_token
        """
        args = {
            'fields': 'likes.summary(true){pic_small,name,id,can_post},picture,name',
            'limit': '500'
        }
        res = GraphAPIRequest(access_token, '/me/videos', args).get_all()
        return res

    @staticmethod
    def get_user_posts(fb_id, access_token):
        """
            return all user photos by access_token
        """
        args = {
            'fields': 'likes.summary(true){pic_small,name,id,can_post},picture,name',
            'limit': '500'
        }
        res = GraphAPIRequest(access_token, '/me/posts', args).get_all()
        return res
