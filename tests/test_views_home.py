import unittest
# import transaction
# from pyramid import testing
# from fas.models import DBSession
import transaction

from tests import BaseTest

'''
class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from fas.models import (
            Base,
            )
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            #model = MyModel(name='one', value=55)
            #DBSession.add(model)
            pass

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_it(self):
        from fas.views.home import Home
        request = testing.DummyRequest()
        info = Home(request)
        self.assertEqual(info['one'].name, 'one')
        self.assertEqual(info['project'], 'fas')
'''


class ViewsHomeFunctionalTests(BaseTest):
    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue(
            '<title>The Fedora Project Account System</title>' in res.body)

    def test_login_get(self):
        res = self.testapp.get('/login', status=200)
        self.assertTrue('<div class="card-view login-container">' in res.body)

    def test_login_post_disabled_account(self):
        form = {'form.submitted': True,
                'login': 'bob',
                'password': 'test12', }
        headers = [('User-Agent', 'Python/Unittests'), ]
        res = self.testapp.post('/login', form, headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue('<div class="card-view login-container">' in res.body)

    def test_login_post_enabled_account(self):
        form = {'form.submitted': True,
                'login': 'jerry',
                'password': 'test12', }
        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        res = self.testapp.post('/login', form, headers)
        self.assertEqual(res.status_code, 302)
        exp_str = 'The resource was found at /; you should be redirected automatically.'
        self.assertTrue(exp_str in res.body)

    def test_login_enabled_account_wrong_credentials(self):
        form = {'form.submitted': True,
                'login': 'jerry',
                'password': 'wrong_creds', }

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        res = self.testapp.post('/login', form, headers)
        self.assertEqual(res.status_code, 200)
        exp_str = '<strong>WOooops!</strong> Login failed'
        self.assertTrue(exp_str in res.body)

    def test_login_pending_account(self):
        form = {'form.submitted': True,
                'login': 'mike',
                'password': 'test12', }
        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        res = self.testapp.post('/login', form, headers)
        self.assertEqual(res.status_code, 200)
        exp_str = 'Login failed, your account has not been validated '
        self.assertTrue(exp_str in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ViewsHomeFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
