# TODO:  Confirm that the formatting is similar to Discords.
# import logging
from uuid import uuid4, uuid5

# from flask import session
from flask_dance.consumer.backend import BaseBackend
# from flask_dance.contrib.gitlab import gitlab

from pysite.constants import OAUTH_GITLAB_DATABASE


class OAuthBackendGitlab(BaseBackend):
    """
    This is the backend for the Gitlab oauth

    This is used to manage users that have completed
    an oauth dance. It contains 3 functions: get, set,
    and delete.  Only set is used.

    Inherits:
        flake_dance.consumer.backend.BaseBackend
        pysite.mixins.DBmixin

    Properties:
        key: The app's secret, we use it to make session IDs
    """

    def __init__(self, manager):
        super().__init__()
        self.db = manager.db
        self.key = manager.app.secret_key
        self.db.create_table(OAUTH_GITLAB_DATABASE, primary_key="id")

    def get(selfself, *args, **kwargs):  # Not used
        pass

    def set(self, blueprint, token):
        user = self.get_user()
        sess_id = str(uuid5(uuid4(), self.key))
        self.add_user(token, user, sess_id)

    def delete(self, blueprint):
        pass
