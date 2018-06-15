from flask import abort, jsonify
from schema import And, Optional, Schema

from pysite.base_route import APIView
from pysite.decorators import ValidationTypes, api_key, api_params
from pysite.mixins import DBMixin, RMQMixin


GET_SCHEMA = Schema({
    Optional('id'): str
})

POST_SCHEMA = Schema({
    'content': And(str, len, error="Announcement content must be a non-empty string"),
    'title': And(str, len, error="Announcement title must be a non-empty string"),
    Optional('public'): bool
})


class AnnouncementManagementAPI(APIView, DBMixin, RMQMixin):
    path = "/announcements"
    name = "api.announcements"
    table_name = "announcements"

    @api_key
    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params: dict):
        """
        Fetch all announcements from the database, returned as
        a list of the announcements in the form:
        [
            {
                'id': 'my-announcement-id',
                'title': "Totally a serious announcement",
                'content': "Example announcement content"
            },
            ...
        ]
        Keep in mind that if no announcements exists, this returns
        an empty list.

        If a parameter `id` is given, return the announcement
        for the given ID in the following form:.
        {
            'id': 'totally-random-sequence-of-characters',
            'title': "Definitely not an example announcement",
            'content': "Absolutely meaningful and interesting content"
        }
        If no announcement with the given ID was found,
        returns an empty dictionary:
        {}

        The ID must be provided as parameter, if exact lookup is desired.
        API key must be provided as header.
        """

        if 'id' in params:
            result = self.db.get(
                self.table_name,
                params['id']
            ) or {}
        else:
            result = self.db.get_all(self.table_name)

        return jsonify(result)

    @api_key
    @api_params(schema=POST_SCHEMA, validation_type=ValidationTypes.json)
    def post(self, announcement: dict):
        """
        Add a new announcement to the database.

        This endpoint expects data in the following format:
        {
            'content': str # The announcement content, Markdown is supported
            'title': str  # The announcement title, a non-empty string,
            'public': bool  # Whether the announcement is public. Optional, defaults to False.
        }

        Data must be provided as JSON.
        API key must be provided as header.
        """

        announcement.setdefault('public', False)
        result = self.db.insert(
            self.table_name,
            announcement,
            return_changes=True
        )
        return jsonify({
            'created_id': result['generated_keys'][0],
            'status': 'ok'
        })
