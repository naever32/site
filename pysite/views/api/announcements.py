from flask import jsonify
from schema import And, Schema, Optional

from pysite.base_route import APIView
from pysite.decorators import api_key, api_params, ValidationTypes
from pysite.mixins import DBMixin, RMQMixin


ANNOUNCEMENT_SCHEMA = Schema({
    'content': And(str, len, error="Announcement content must be a non-empty string"),
    'title': And(str, len, error="Announcement title must be a non-empty string"),
    Optional('public', default=False): bool
})


class AnnouncementManagementAPI(APIView, DBMixin, RMQMixin):
    path = "/announcements"
    name = "api.announcements"
    table_name = "announcements"

    @api_key
    @api_params(schema=ANNOUNCEMENT_SCHEMA, validation_type=ValidationTypes.json)
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

        result = self.db.insert(
            self.table_name,
            announcement,
            return_changes=True
        )
        return jsonify({
            'created_id': result['generated_keys'][0],
            'status': 'ok'
        })
