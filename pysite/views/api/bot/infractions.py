import datetime
from typing import NamedTuple

import rethinkdb
from flask import jsonify
from schema import Optional, Schema

from pysite.base_route import APIView
from pysite.constants import ValidationTypes
from pysite.decorators import api_params
from pysite.mixins import DBMixin

# todo: add @api_key annotation to all methods!

"""
INFRACTIONS API

"GET" endpoints in this API may take the following optional parameters, depending on the endpoint:
  - active: filters infractions that are active (true), expired (false), or either (not present/any)
  - expand: expands the result data with the information about the users (slower)

Endpoints:

  GET /bot/infractions
    Gets a list of all infractions, regardless of type or user.
    Parameters: "active", "expand".
    This endpoint returns an array of infraction objects.

  GET /bot/infractions/user/<user_id>
    Gets a list of all infractions for a user.
    Parameters: "active", "expand".
    This endpoint returns an array of infraction objects.

  GET /bot/infractions/type/<type>
    Gets a list of all infractions of the given type (ban, mute, etc.)
    Parameters: "active", "expand".
    This endpoint returns an array of infraction objects.

  GET /bot/infractions/user/<user_id>/<type>
    Gets a list of all infractions of the given type for a user.
    Parameters: "active", "expand".
    This endpoint returns an array of infraction objects.

  GET /bot/infractions/user/user_id>/<type>/current
    Gets the active infraction (if any) of the given type for a user.
    Parameters: "expand".
    This endpoint returns an object with the "infraction" key, which is either set to null (no infraction)
      or the query's corresponding infraction. It will not return an infraction if the type of the infraction
      isn't duration-based (e.g. kick, warning, etc.)

  GET /bot/infractions/id/<infraction_id>
    Gets the infraction (if any) for the given ID.
    Parameters: "expand".
    This endpoint returns an object with the "infraction" key, which is either set to null (no infraction)
      or the infraction corresponding to the ID.

  POST /bot/infractions
  Creates an infraction for a user.
  Parameters (JSON payload):
    "type" (str): the type of the infraction (must be a valid infraction type).
    "reason" (str): the reason of the infraction.
    "user_id" (str): the Discord ID of the user who is being given the infraction.
    "actor_id" (str): the Discord ID of the user who submitted the infraction.
    "duration" (optional int): the duration, in seconds, of the infraction. This is ignored for infractions
      which are not duration-based. For other infraction types, omitting this field may imply permanence.
    "expand" (optional bool): whether to expand the infraction user data once the infraction is inserted and returned.
"""


class InfractionType(NamedTuple):
    timed_infraction: bool  # whether the infraction is active until it expires.


INFRACTION_TYPES = {
    "warning": InfractionType(timed_infraction=False),
    "mute": InfractionType(timed_infraction=True),
    "ban": InfractionType(timed_infraction=True),
    "kick": InfractionType(timed_infraction=False),
    "softban": InfractionType(timed_infraction=False)
}

GET_SCHEMA = Schema({
    Optional("active"): str,
    Optional("expand"): str
})

GET_ACTIVE_SCHEMA = Schema({
    Optional("expand"): str
})

CREATE_INFRACTION_SCHEMA = Schema({
    "type": lambda tp: tp in INFRACTION_TYPES,
    "reason": str,
    "user_id": str,  # Discord user ID
    "actor_id": str,  # Discord user ID
    Optional("duration"): int,  # In seconds. If not provided, may imply permanence depending on the infraction
    Optional("expand"): bool
})


class InfractionsView(APIView, DBMixin):
    path = "/bot/infractions"
    name = "bot.infractions"
    table_name = "bot_infractions"

    @api_params(schema=GET_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params=None):
        return _infraction_list_filtered(self, params, {})

    @api_params(schema=CREATE_INFRACTION_SCHEMA, validation_type=ValidationTypes.json)
    def post(self, data):
        deactivate_infraction_query = None

        infraction_type = data["type"]
        user_id = data["user_id"]
        actor_id = data["actor_id"]
        reason = data["reason"]
        duration = data.get("duration")
        expand = data.get("expand")
        expires_at = None
        inserted_at = datetime.datetime.now(tz=datetime.timezone.utc)

        # check if the user already has an active infraction of this type
        # if so, we need to disable that infraction and create a new infraction
        if INFRACTION_TYPES[infraction_type].timed_infraction:
            active_infraction_query = \
                self.db.query(self.table_name).merge(_merge_active_check()) \
                    .filter({"user_id": user_id, "type": infraction_type, "active": True}) \
                    .limit(1).nth(0).default(None)

            active_infraction = self.db.run(active_infraction_query)
            if active_infraction:
                deactivate_infraction_query = \
                    self.db.query(self.table_name) \
                        .get(active_infraction["id"]) \
                        .update({"active": False})

            if duration:
                expires_at = inserted_at + datetime.timedelta(seconds=duration)

        infraction_insert_doc = {
            "actor_id": actor_id,
            "user_id": user_id,
            "type": infraction_type,
            "reason": reason,
            "inserted_at": inserted_at,
            "expires_at": expires_at
        }

        infraction_id = self.db.insert(self.table_name, infraction_insert_doc)["generated_keys"][0]

        if deactivate_infraction_query:
            self.db.run(deactivate_infraction_query)

        query = self.db.query(self.table_name).get(infraction_id) \
            .merge(_merge_expand_users(self, expand)) \
            .merge(_merge_active_check()) \
            .without("user_id", "actor_id").default(None)
        return jsonify({
            "infraction": self.db.run(query)
        })


class InfractionById(APIView, DBMixin):
    path = "/bot/infractions/id/<string:infraction_id>"
    name = "bot.infractions.id"
    table_name = "bot_infractions"

    @api_params(schema=GET_ACTIVE_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params, infraction_id):
        params = params or {}
        expand = parse_bool(params.get("expand"), default=False)

        query = self.db.query(self.table_name).get(infraction_id) \
            .merge(_merge_expand_users(self, expand)) \
            .merge(_merge_active_check()) \
            .without("user_id", "actor_id").default(None)
        return jsonify({
            "infraction": self.db.run(query)
        })


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


class CurrentInfractionByTypeAndUserView(APIView, DBMixin):
    path = "/bot/infractions/user/<string:user_id>/<string:type>/current"
    name = "bot.infractions.user.type.current"
    table_name = "bot_infractions"

    @api_params(schema=GET_ACTIVE_SCHEMA, validation_type=ValidationTypes.params)
    def get(self, params, user_id, type):
        params = params or {}
        expand = parse_bool(params.get("expand"), default=False)

        query_filter = {
            "user_id": user_id,
            "type": type
        }
        query = _merged_query(self, expand, query_filter).filter({
            "active": True
        }).limit(1).nth(0).default(None)
        return jsonify({
            "infraction": self.db.run(query)
        })


def _infraction_list_filtered(view, params=None, query_filter=None):
    params = params or {}
    query_filter = query_filter or {}
    active = parse_bool(params.get("active"))
    expand = parse_bool(params.get("expand"), default=False)

    if active is not None:
        query_filter["active"] = active

    query = _merged_query(view, expand, query_filter)
    return jsonify(view.db.run(query.coerce_to("array")))


def _merged_query(view, expand, query_filter):
    return view.db.query(view.table_name).merge(_merge_active_check()).filter(query_filter) \
        .merge(_merge_expand_users(view, expand)).without("user_id", "actor_id")


def _merge_active_check():
    # Checks if the "active" field has been set to false (manual infraction removal).
    # If not, the "active" field is set to whether the infraction has expired.
    def _merge(row):
        return {
            "active":
                rethinkdb.branch(
                    _is_timed_infraction(row["type"]),
                    rethinkdb.branch(
                        row["active"].default(True).eq(False),
                        False,
                        rethinkdb.branch(
                            row["expires_at"].eq(None),
                            True,
                            row["expires_at"] > rethinkdb.now()
                        )
                    ),
                    False
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


def _is_timed_infraction(type_var):
    # this method generates an ReQL expression to check if the given type
    # is a "timed infraction" (i.e it can expire or be permanent)

    timed_infractions = filter(lambda key: INFRACTION_TYPES[key].timed_infraction, INFRACTION_TYPES.keys())
    expr = rethinkdb.expr(False)
    for infra_type in timed_infractions:
        if expr is None:
            expr = type_var.eq(infra_type)
        else:
            expr = expr | type_var.eq(infra_type)
    return expr


def parse_bool(a_string, default=None):
    # Not present, null or any: returns default (defaults to None)
    # false, no, or 0: returns False
    # anything else: True
    if a_string is None or a_string == "null" or a_string == "any":
        return default
    if a_string.lower() == "false" or a_string.lower() == "no" or a_string == "0":
        return False
    return True
