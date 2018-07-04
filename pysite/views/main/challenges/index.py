import json
import math
from json import JSONDecodeError
from typing import Dict

import rethinkdb
from flask import request, url_for
from werkzeug.exceptions import NotFound

from pysite.base_route import RouteView
from pysite.mixins import DBMixin

CHALLENGES_PER_PAGE = 4


class ChallengesIndexView(RouteView, DBMixin):
    path = "/challenges"
    name = "challenges.index"
    table_name = "challenges"

    def get(self):
        filter_raw = request.args.get("filter", default=str({}))
        page_number = request.args.get("page", default=1, type=int)

        if page_number < 1:
            raise NotFound()

        page_slice = ((page_number - 1) * CHALLENGES_PER_PAGE, page_number * CHALLENGES_PER_PAGE)

        try:
            active_filter = json.loads(filter_raw)
        except JSONDecodeError:
            active_filter = {}

        query_filter = {}

        if "difficulty" in active_filter:
            query_filter["difficulty"] = active_filter["difficulty"].lower()

        # it is known: the uglier the query, the more faster it be going
        challenge_filter_query = self.db.query(self.table_name).filter(
            query_filter
        ).coerce_to("array").do(lambda filter_result: {
            "total_item_count": filter_result.count(),
            "page_content": filter_result.order_by(rethinkdb.desc("date")).slice(*page_slice).merge(
                lambda challenge: {
                    "author": self.db.query("users").get(challenge["author_id"])
                }
            )
        })
        challenge_filter_result = self.db.run(challenge_filter_query)
        total_page_count = math.ceil(challenge_filter_result["total_item_count"] / CHALLENGES_PER_PAGE)
        challenges = challenge_filter_result["page_content"]

        return self.render(
            "main/challenges/index.html", filter=active_filter, filter_url=self.filter_url,
            filter_match=self.filter_match, challenges=challenges, total_page_count=total_page_count,
            pagination=self.pagination, page_number=page_number
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

    def pagination(self, page, pages, active_filter):
        result = [{"num": i,
                   "url": url_for(self.name, page=i, filter=json.dumps(active_filter)),
                   "active": page == i
                   } for i in range(1, pages + 1)]
        # add prev/next arrows
        result.insert(0, {
            "num": "previous",
            "url": url_for(self.name, page=page - 1, filter=json.dumps(active_filter)) if page > 1 else "#",
            "disabled": page == 1,
            "active": False
        })
        result.append({
            "num": "next",
            "url": url_for(self.name, page=page + 1, filter=json.dumps(active_filter)) if page < pages else "#",
            "disabled": page == pages,
            "active": False
        })
        return result
