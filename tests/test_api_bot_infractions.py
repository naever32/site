import json

from tests import SiteTest, app


class ApiBotInfractionsEndpoint(SiteTest):

    def test_infraction_create(self):
        # Invalid infraction type
        post_data_invalid_type = json.dumps(
            {"type": "not_a_type", "reason": "test", "user_id": "abc", "actor_id": "abc"}
        )
        response = self.client.post("/bot/infractions", app.config["API_SUBDOMAIN"],
                                    headers=app.config["TEST_HEADER"],
                                    data=post_data_invalid_type)
        self.assert400(response)

        # Kick infraction
        post_data_valid = json.dumps(
            {"type": "kick", "reason": "test", "user_id": "test", "actor_id": "test"}
        )
        response = self.client.post("/bot/infractions", app.config["API_SUBDOMAIN"],
                                    headers=app.config["TEST_HEADER"],
                                    data=post_data_valid)
        self.assert200(response)
        self.assertTrue("infraction" in response.json)
        self.assertTrue("id" in response.json["infraction"])
        kick_infraction_id = response.json["infraction"]["id"]
        response = self.client.get(f"/bot/infractions/id/{kick_infraction_id}", app.config["API_SUBDOMAIN"],
                                   headers=app.config["TEST_HEADER"])
        self.assert200(response)
        self.assertTrue("infraction" in response.json)
        self.assertTrue("id" in response.json["infraction"])
        self.assertEqual(response.json["infraction"]["id"], kick_infraction_id)
        self.assertTrue("active" in response.json["infraction"])
        self.assertFalse(response.json["infraction"]["active"])
