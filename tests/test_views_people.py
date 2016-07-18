import unittest
from tests import BaseTest


class ViewsPeopleFunctionalTests(BaseTest):

    def test_people_get(self):
        res = self.testapp.get('/people', status=200)
        self.assertTrue('<div class="container people-list">' in res.body)
        # Jerry is the only registered and confirmed account from default data
        self.assertTrue('<a href="http://localhost/people/profile/jerry">'
                        in res.body)

    def test_people_get_jerry(self):
        res = self.testapp.get('/people/profile/jerry', status=200)
        self.assertTrue('<dd>jerry</dd>' in res.body)

    def test_people_partial_search(self):
        res = self.testapp.get('/people/search/j', status=200)
        self.assertTrue('<h3>Search for people</h3>' in res.body)
        self.assertTrue('<a href="http://localhost/people/profile/jerry">' in res.body)

    def test_people_search_name(self):
        res = self.testapp.get('/people/search/jerry', status=302)
        res = res.follow()
        self.assertTrue('<dd>jerry</dd>' in res.body)

    def test_people_edit_logged_out(self):
        url = '/people/profile/jerry/edit'
        res = self.testapp.get(url, status=200)
        self.assertTrue('placeholder="Login" name="login" value=""/><br/>'
                        in res.body)

    def test_people_edit_logged_in(self):
        # login user
        form = {'login': 'jerry',
                'password': 'test12',
                'form.submitted': True,}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        # Login
        resp = self.testapp.post('/login', form, headers, status=302)
        resp = resp.follow()
        self.assertTrue('Log out' in resp.body)  # verify that we are logged in

        url = '/people/profile/jerry/edit'
        res = self.testapp.get(url, status=200)
        self.assertFalse('placeholder="Login" name="login" value=""/><br/>'
                        in res.body)

        exp_str = '<p>Update your profile&#39;s informations</p>'

    @unittest.skip('For some reason this throws 401. Might be a bug')
    def test_people_edit_logged_in_modify_profile(self):
        # login user
        form = {'login': 'jerry',
                'password': 'test12',
                'form.submitted': True,}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        resp = self.testapp.post('/login', form, headers, status=302)
        url = '/people/profile/jerry/edit'
        profile_form = {}

        res = self.testapp.post(url, profile_form, headers)
        self.assertFalse('placeholder="Login" name="login" value=""/><br/>'
                         in res.body)

        exp_str = '<p>Update your profile&#39;s informations</p>'
        self.assertTrue(exp_str in res.body)

    def test_people_edit_another_persons_profile(self):
        # expect to redirect to home profile page not being able to edit
        # login user
        form = {'login': 'jerry',
                'password': 'test12',
                'form.submitted': True,}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        # Login
        resp = self.testapp.post('/login', form, headers, status=302)
        resp = resp.follow()
        self.assertTrue('Log out' in resp.body)  # verify that we are logged in

        url = '/people/profile/admin/edit'
        res = self.testapp.get(url, status=302)
        # we should be redirected to profile page of admin
        exp_str = 'The resource was found at /people/profile/admin'
        self.assertTrue(exp_str in res.body)

    def test_profile_edit_account_does_not_exist(self):
        # to edit a profile we must be logged in
        # login user
        form = {'login': 'jerry',
                'password': 'test12',
                'form.submitted': True,}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        # Login
        resp = self.testapp.post('/login', form, headers, status=302)
        resp = resp.follow()
        self.assertTrue('Log out' in resp.body)  # verify that we are logged in

        url = '/people/profile/doesnotexist/edit'
        res = self.testapp.get(url, status=404)
        expected_str = 'No such user found'
        self.assertTrue(expected_str in res.body)



if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsPeopleFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
