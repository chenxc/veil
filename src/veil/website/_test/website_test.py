from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
from sandal.fixture import fixtures
from sandal.fixture import UsingFixture
from veil.http import *
from ..routing import route

context = None

__import__('veil.browser')

class WebsiteTest(UsingFixture):
    def test_routing(self):
        @route('GET', '/hello', website='test')
        def hello():
            return 'hello'

        browser = fixtures.start_website_and_browser('test')
        browser.get('/', expected_status_code=httplib.NOT_FOUND)
        self.assertEqual('hello', browser.get('/hello').response_text)

    def test_context_manager(self):

        @route('GET', '/context', website='test')
        def report_context():
            return context or ''

        @contextlib.contextmanager
        def set_context_being(some_context):
            global context
            context = some_context
            try:
                yield
            finally:
                context = None

        browser = fixtures.start_website_and_browser(
            'test', context_managers=[create_stack_context(set_context_being, 'hello')])
        self.assertEqual('hello', browser.get('/context').response_text)


