import json
from json import JSONDecodeError
from typing import Dict

from flask import url_for, request

from pysite.base_route import RouteView
from pysite.mixins import DBMixin


class ChallengesIndexView(RouteView, DBMixin):
    path = "/challenges"
    name = "challenges.index"
    table_name = "challenges"

    def get(self):
        filter_raw = request.args.get("filter", default="{}")
        page_number = request.args.get("page", default=1, type=int)

        try:
            active_filter = json.loads(filter_raw)
        except JSONDecodeError:
            active_filter = {}

        return self.render(
            "main/challenges/index.html", filter=active_filter, filter_url=self.filter_url,
            filter_match=self.filter_match
        )

    def filter_url(self, current_filter: Dict, filter_changes: Dict):
        new_filter = dict(current_filter)
        for key, val in filter_changes.items():
            if val is None and key in new_filter:
                del new_filter[key]
            elif val is not None:
                new_filter[key] = val
        return url_for(self.name, filter=json.dumps(new_filter))

    @staticmethod
    def filter_match(current_filter, sub_filter):
        for key, val in sub_filter.items():
            if val is None and key in current_filter and current_filter[key] is not None:
                return False
            if val is not None and key not in current_filter:
                return False
            if val is not None and key in current_filter and current_filter[key] != val:
                return False

        return True
