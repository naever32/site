from flask import jsonify

from pysite.base_route import APIView
from pysite.decorators import csrf
from pysite.mixins import DBMixin


class CountdownView(APIView, DBMixin):
    path = "/jams/countdown"
    name = "jams.countdown"

    @csrf
    def get(self):
        # Get the record for the latest Code Jam.
        code_jam = self.db.run(
            self.db.query("code_jams")
            .max("number")
        )

        # Used for shorthand to improve readability.
        start = code_jam["date_start"]
        end = code_jam["date_end"]

        # Return the starting and ending dates for the latest Code Jam.
        return jsonify({
            "number": code_jam["number"],
            "date_start": {
                "year": start.year,
                "month": start.month,
                "day": start.day,
                "hours": start.hour,
                "minutes": start.minute,
                "seconds": start.second
            },
            "date_end": {
                "year": end.year,
                "month": end.month,
                "day": end.day,
                "hours": end.hour,
                "minutes": end.minute,
                "seconds": end.second
            }
        })
