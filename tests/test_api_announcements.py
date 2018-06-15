import json

from tests import SiteTest, app


class EmptyDatabaseAnnouncementLookup(SiteTest):
    def test_getting_all_announcements_returns_empty_list(self):
        response = self.client.get(
            '/announcements',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        # FIXME: `SiteTest`s should probably be isolated from each other, but
        #        they apparently are not. Once they are, check equality against
        #        an empty list instead of checking for the class instance,
        #        because currently, there might be other objects in the database.
        self.assertIsInstance(response.json, list)

    def test_exact_random_lookup_returns_empty_dict(self):
        response = self.client.get(
            '/announcements?id=whatever',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER'],
        )
        self.assert200(response)
        self.assertEqual(response.json, {})

    def test_delete_random_announcement_returns_deleted_0(self):
        response = self.client.delete(
            '/announcements?id=whatever',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )
        self.assert200(response)
        self.assertEqual(response.json, {'deleted': 0})


class AnnouncementCreation(SiteTest):
    announcement_data = {
        'title': "On the health effects of eating raw lemons",
        'content': "For years, experts have wondered about effects of eating uncooked lemons."
    }

    def setUp(self):
        post_data = json.dumps(self.announcement_data)

        response = self.client.post(
            '/announcements',
            app.config['API_SUBDOMAIN'],
            data=post_data,
            headers=app.config['TEST_HEADER']
        )

        self.assert200(response)
        self.assertEqual(response.json['status'], 'ok')
        self.assertIsInstance(response.json['created_id'], str)
        self.created_id = response.json['created_id']

    def test_can_lookup_announcement(self):
        response = self.client.get(
            f'/announcements?id={self.created_id}',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )

        self.assert200(response)
        self.assertEqual(response.json['title'], self.announcement_data['title'])
        self.assertEqual(response.json['content'], self.announcement_data['content'])
        self.assertFalse(response.json['public'])
        self.assertEqual(response.json['id'], self.created_id)

    def test_announcement_in_all_announcements(self):
        response = self.client.get(
            '/announcements',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )

        self.assert200(response)
        self.assertIn(self.created_id, (announcement['id'] for announcement in response.json))


class AnnouncementDeletion(SiteTest):
    announcement_data = {
        'title': "On the health effects of eating raw lemons",
        'content': "For years, experts have wondered about effects of eating uncooked lemons."
    }

    def setUp(self):
        post_data = json.dumps(self.announcement_data)

        response = self.client.post(
            '/announcements',
            app.config['API_SUBDOMAIN'],
            data=post_data,
            headers=app.config['TEST_HEADER']
        )
        self.created_id = response.json['created_id']

    def test_deleting_unknown_id_returns_deleted_0(self):
        response = self.client.delete(
            '/announcements?id=whatever',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )

        self.assert200(response)
        self.assertEqual(response.json, {'deleted': 0})

    def test_deleting_created_id_returns_deleted_1(self):
        response = self.client.delete(
            f'/announcements?id={self.created_id}',
            app.config['API_SUBDOMAIN'],
            headers=app.config['TEST_HEADER']
        )

        self.assert200(response)
        self.assertEqual(response.json, {'deleted': 1})
