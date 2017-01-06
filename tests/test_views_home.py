import unittest
from tests import BaseTest


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
        exp_str = 'Login failed, your account has not been validated'
        self.assertTrue(exp_str in res.body)

    def test_logout(self):
        res = self.testapp.get('/logout', status=302)
        exp_str = 'The resource was found at http://localhost/logout;'
        self.assertTrue(exp_str in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ViewsHomeFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
