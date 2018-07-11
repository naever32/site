import rethinkdb
from flask import jsonify
from schema import Schema, Optional

from pysite.base_route import APIView
from pysite.constants import ValidationTypes
from pysite.decorators import api_params
from pysite.mixins import DBMixin

GET_SCHEMA = Schema({
    Optional("user"): str,  # filters the infractions for the particular user
    Optional("active"): str,  # filters infractions that are active (true), expired (false), or either (not present/any)
    Optional("expand"): str  # expands the result data with the information about the users (slower)
})


class InfractionsView(APIView, DBMixin):
    path = "/bot/infractions"
    name = "bot.infractions"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params=None):
        user_id = params.get("user")
        active = parse_bool(params.get("active"))
        expand = parse_bool(params.get("expand"), default=False)

        query_filter = {}
        if active is not None:
            query_filter["active"] = active

        if user_id:
            # get infractions for this user only
            query_filter["user_id"] = user_id

        query = self.db.query(self.table_name).merge(self._default_merge(expand)).filter(query_filter) \
            .without("user_id", "actor_id")
        return jsonify(self.db.run(query.coerce_to("array")))

    def _default_merge(self, expand):
        def _merge(row):
            def _do_expand(user_id):
                # Expands the user information, if it is in the database.

                if expand:
                    return self.db.query("users").get(user_id).default({
                        "user_id": user_id
                    })

                return {
                    "user_id": user_id
                }

            def _do_active_check(row):
                # Checks if the "active" field has been set to false (manual infraction removal).
                # If not, the "active" field is set to whether the infraction has expired.

                return rethinkdb.branch(
                    row["active"].default(True).eq(False),
                    False,
                    rethinkdb.branch(
                        row["expires_at"].eq(None),
                        True,
                        row["expires_at"] > rethinkdb.now()
                    )
                )

            # expand users and override the active field
            merge_dict = {
                "user": _do_expand(row["user_id"]),
                "actor": _do_expand(row["actor_id"]),
                "active": _do_active_check(row)
            }

            return merge_dict

        return _merge


def parse_bool(a_string, default=None):
    if a_string is None or a_string == "null" or a_string == "any":
        return default
    if a_string.lower() == "false" or a_string.lower() == "no" or a_string == "0":
        return False
    return True
