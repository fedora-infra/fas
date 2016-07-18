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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsPeopleFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
