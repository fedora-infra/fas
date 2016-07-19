import unittest
from tests import BaseTest


class ViewsAdminFunctionalTests(BaseTest):
    def login_helper(self):
        # to edit a profile we must be logged in
        # login user
        form = {'login': 'admin',
                'password': 'admin',
                'form.submitted': True,}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        # Login
        resp = self.testapp.post('/login', form, headers, status=302)
        resp = resp.follow()
        self.assertTrue('Log out' in resp.body)  # verify that we are logged in

    def test_get_admin(self):
        self.login_helper()
        res = self.testapp.get('/settings', status=200)
        # verify the admin panel is present
        self.assertTrue('registered members' in res.body)
        self.assertTrue('active groups' in res.body)
        self.assertTrue('licenses agreement' in res.body)
        self.assertTrue('trusted applications' in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsAdminFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
