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
        self.assertEqual(response.json, [])

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
