"""Tests the `/api/bot/off-topic-names` endpoint."""

from tests import SiteTest, app


class EmptyDatabaseOffTopicEndpointTests(SiteTest):
    """Tests fetching all entries from the endpoint with an empty database."""

    def test_get_returns_empty_list(self):
        response = self.client.get(
            '/bot/off-topic-names',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertEqual(response.json, [])


class AddingANameOffTopicEndpointTests(SiteTest):
    """Tests adding a channel name to the database."""

    def test_returns_400_on_bad_data(self):
        response = self.client.post(
            '/bot/off-topic-names?name=my%20TOTALLY%20VALID%20CHANNE%20NAME',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert400(response)

    def test_can_add_new_package(self):
        response = self.client.post(
            '/bot/off-topic-names?name=lemons-lemon-shop',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)


class AddingChannelNameToDatabaseEndpointTests(SiteTest):
    """Tests fetching names from the database with GET."""

    CHANNEL_NAME = 'bisks-disks'

    def setUp(self):
        response = self.client.post(
            f'/bot/off-topic-names?name={self.CHANNEL_NAME}',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)

    def test_name_is_in_all_entries(self):
        response = self.client.get(
            '/bot/off-topic-names',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertIn(self.CHANNEL_NAME, response.json)
