import json

from tests import SiteTest, app


class AnnouncementsAPITests(SiteTest):
    def test_can_create_normal_announcement(self):
        post_data = json.dumps({
            'title': "On the health effects of eating raw lemons",
            'content': "For years, experts have wondered about effects of eating uncooked lemons."
        })

        response = self.client.post(
            '/announcements',
            app.config['API_SUBDOMAIN'],
            data=post_data,
            headers=app.config['TEST_HEADER']
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ok')
        self.assertIsInstance(response.json['created_id'], str)
