import json

from tests import SiteTest, app


class EmptyDatabaseEndpointTests(SiteTest):
    def test_api_docs_get_all(self):
        response = self.client.get(
            '/bot/bigbrother',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertIsInstance(response.json, list)

    def test_invalid_user_id_returns_400(self):
        response = self.client.get(
            '/bot/bigbrother?user_id=lemon-is-not-a-number',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert400(response)
        self.assertIsInstance(response.json['message'], str)

    def test_fetching_single_entry_returns_404(self):
        response = self.client.get(
            '/bot/bigbrother?user_id=01932',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert404(response)
        self.assertIsInstance(response.json['message'], str)


class AddingAnEntryEndpointTests(SiteTest):
    GOOD_DATA = {
        'user_id': 42,
        'channel_id': 55
    }
    GOOD_DATA_JSON = json.dumps(GOOD_DATA)

    def setUp(self):
        response = self.client.post(
            '/bot/bigbrother',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER'],
            data=self.GOOD_DATA_JSON
        )
        self.assertEqual(response.status_code, 204)

    def test_entry_is_in_all_entries(self):
        response = self.client.get(
            '/bot/bigbrother',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertIn(self.GOOD_DATA, response.json)

    def test_can_fetch_entry_with_param_lookup(self):
        response = self.client.get(
            f'/bot/bigbrother?user_id={self.GOOD_DATA["user_id"]}',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertEqual(response.json, self.GOOD_DATA)


class UpdatingAnEntryEndpointTests(SiteTest):
    ORIGINAL_DATA = {
        'user_id': 300,
        'channel_id': 400
    }
    ORIGINAL_DATA_JSON = json.dumps(ORIGINAL_DATA)
    UPDATED_DATA = {
        'user_id': 300,
        'channel_id': 500
    }
    UPDATED_DATA_JSON = json.dumps(UPDATED_DATA)

    def setUp(self):
        response = self.client.post(
            '/bot/bigbrother',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER'],
            data=self.ORIGINAL_DATA_JSON
        )
        self.assertEqual(response.status_code, 204)

    def test_can_update_data(self):
        response = self.client.post(
            '/bot/bigbrother',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER'],
            data=self.UPDATED_DATA_JSON
        )
        self.assertEqual(response.status_code, 204)
