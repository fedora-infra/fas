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
        resp = self.testapp.post('/login', form, headers, status=302)
        url = '/people/profile/jerry/edit'
        res = self.testapp.get(url, status=200)
        self.assertFalse('placeholder="Login" name="login" value=""/><br/>'
                        in res.body)

        exp_str = '  <form method="POST" action="http://localhost/people/' \
                  'profile/jerry/edit" class="form-horizontal" role="form">'
        self.assertTrue(exp_str in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsPeopleFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
