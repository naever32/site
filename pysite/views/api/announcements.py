from flask import jsonify
from schema import And, Optional, Schema

from pysite.base_route import APIView
from pysite.decorators import ValidationTypes, api_key, api_params
from pysite.mixins import DBMixin, RMQMixin


GET_SCHEMA = Schema({
    Optional('id'): str
})

POST_SCHEMA = Schema({
    'title': And(str, len, error="Announcement title must be a non-empty string"),
    'content_md': And(str, len, error="Announcement content must be a non-empty string")
})

DELETE_SCHEMA = Schema({
    'id': str
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
                'content_md': "Example announcement content"
                'content_html': "Example announcement content"
                'content_rst': "Example announcement content"
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
            'content_md': "Absolutely meaningful and interesting content"
            'content_rst': "I have no idea how to write RST",
            'content_html': ... # <rendered RST>
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
    def post(self, data: dict):
        """
        Add a new announcement draft to the database.

        This endpoint expects data in the following format:
        {
            'content_md': str # The announcement content for the initial draft, as Markdown.
            'title': str  # The announcement title, a non-empty string
        }

        Data must be provided as JSON.
        API key must be provided as header.
        """

        data = {
            'title': data['title'],
            'content_md': data['content_md'],
            'content_rst': "",
            'content_html': "",
            'public': False
        }

        result = self.db.insert(
            self.table_name,
            data,
            return_changes=True
        )
        return jsonify({
            'created_id': result['generated_keys'][0],
            'status': 'ok'
        })

    @api_key
    @api_params(schema=DELETE_SCHEMA, validation_type=ValidationTypes.params)
    def delete(self, params: dict):
        """
        Delete an announcement from the database.
        The announcement to delete must be specified with
        the query argument `id`.
        Returns a dictionary containing a single key,
        `deleted`, which is an integer denoting the
        amount of objects deleted by this method,
        either 0 or 1.

        The `id` must be supplied as a parameter.
        API key must be provided as header.
        """

        result = self.db.delete(
            self.table_name,
            params['id'],
            return_changes=True
        )
        return jsonify(deleted=result['deleted'])
