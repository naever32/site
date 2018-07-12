import rethinkdb
from flask import jsonify
from schema import Optional, Schema

from pysite.base_route import APIView
from pysite.constants import ValidationTypes
from pysite.decorators import api_params
from pysite.mixins import DBMixin

"""
INFRACTIONS API

All "GET" endpoints in this API take the following optional parameters:
  - active: filters infractions that are active (true), expired (false), or either (not present/any)
  - expand: expands the result data with the information about the users (slower)

Endpoints:

  GET /bot/infractions
    Gets a list of all infractions, regardless of type or user.

  GET /bot/infractions/user/<user_id>
    Gets a list of all infractions for a user.

  GET /bot/infractions/type/<type>
    Gets a list of all infractions of the given type (ban, mute, etc.)

  GET /bot/infractions/user/<user_id>/<type>
    Gets a list of all infractions of the given type for a user.
"""

GET_SCHEMA = Schema({
    Optional("active"): str,
    Optional("expand"): str
})


class ListInfractionsView(APIView, DBMixin):
    path = "/bot/infractions"
    name = "bot.infractions"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params=None):
        return _infraction_list_filtered(self, params, {})


class ListInfractionsByUserView(APIView, DBMixin):
    path = "/bot/infractions/user/<string:user_id>"
    name = "bot.infractions.user"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params, user_id):
        return _infraction_list_filtered(self, params, {
            "user_id": user_id
        })


class ListInfractionsByTypeView(APIView, DBMixin):
    path = "/bot/infractions/type/<string:type>"
    name = "bot.infractions.type"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params, type):
        return _infraction_list_filtered(self, params, {
            "type": type
        })


class ListInfractionsByTypeAndUserView(APIView, DBMixin):
    path = "/bot/infractions/user/<string:user_id>/<string:type>"
    name = "bot.infractions.user.type"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params, user_id, type):
        return _infraction_list_filtered(self, params, {
            "user_id": user_id,
            "type": type
        })


def _infraction_list_filtered(view, params=None, query_filter=None):
    params = params or {}
    query_filter = query_filter or {}
    active = parse_bool(params.get("active"))
    expand = parse_bool(params.get("expand"), default=False)

    if active is not None:
        query_filter["active"] = active

    query = view.db.query(view.table_name).merge(_merge_active_check()).filter(query_filter) \
        .merge(_merge_expand_users(view, expand)).without("user_id", "actor_id")
    return jsonify(view.db.run(query.coerce_to("array")))


def _merge_active_check():
    # Checks if the "active" field has been set to false (manual infraction removal).
    # If not, the "active" field is set to whether the infraction has expired.
    def _merge(row):
        return {
            "active": rethinkdb.branch(
                row["active"].default(True).eq(False),
                False,
                rethinkdb.branch(
                    row["expires_at"].eq(None),
                    True,
                    row["expires_at"] > rethinkdb.now()
                )
            )
        }

    return _merge


def _merge_expand_users(view, expand):
    def _do_expand(user_id):
        if not user_id:
            return None
        # Expands the user information, if it is in the database.

        if expand:
            return view.db.query("users").get(user_id).default({
                "user_id": user_id
            })

        return {
            "user_id": user_id
        }

    def _merge(row):
        return {
            "user": _do_expand(row["user_id"].default(None)),
            "actor": _do_expand(row["actor_id"].default(None))
        }

    return _merge


def parse_bool(a_string, default=None):
    # Not present, null or any: returns default (defaults to None)
    # false, no, or 0: returns False
    # anything else: True
    if a_string is None or a_string == "null" or a_string == "any":
        return default
    if a_string.lower() == "false" or a_string.lower() == "no" or a_string == "0":
        return False
    return True
