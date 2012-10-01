from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.profile.web import *
from veil.frontend.web.nginx import *
from veil.environment import *
from veil.environment.setting import *
from .browser import start_website_and_browser

if 'test' == VEIL_ENV:
    register_website('test')
    TEST_WEBSITE_SETTINGS = website_settings('test', 5090)
    register_settings_coordinator(lambda settings: add_reverse_proxy_server(settings, 'test'))

PAGE_CONTENT =\
"""
<html>
<head>
<script src="/-test/jquery.js"></script>
<script src="/-test/jquery-cookie.js"></script>
<script src="/-test/veil.js"></script>
</head>
<body>
</body>
</html>
"""

class BrowsingTest(TestCase):
    def test_fail(self):
        @route('GET', '/', website='test')
        def home():
            return PAGE_CONTENT

        with self.assertRaises(AssertionError):
            start_website_and_browser(
                'test', '/',
                ["""
                veil.assertEqual(1, 2);
                """])


    def test_stop(self):
        @route('GET', '/', website='test')
        def home():
            return PAGE_CONTENT

        start_website_and_browser(
            'test', '/',
            ["""
            veil.stopTest();
            """])


