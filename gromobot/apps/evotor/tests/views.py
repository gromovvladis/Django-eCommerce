from django.test import TestCase


class EvotorCloudAuthTestCase(TestCase):
    fixtures = []

    def test_is_valid_site_token(self):
        self.assertEqual(1, 1)
