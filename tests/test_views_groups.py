import unittest
from tests import BaseTest


class ViewsGroupsFunctionalTests(BaseTest):
    def test_get_groups(self):
        res = self.testapp.get('/groups', status=200)
        self.assertTrue('<h1>Fedora Groups&#39; List</h1>' in res.body)
        self.assertTrue('avengers' in res.body)

    def test_get_group_profile(self):
        url = '/group/details/300'  # avengers profile
        res = self.testapp.get(url, status=200)
        self.assertTrue('avengers' in res.body)
        self.assertTrue('shell' in res.body)  # Group Type
        self.assertTrue('Principal Administrator' in res.body)

    def test_group_partial_search(self):
        url = '/group/search/a'
        res = self.testapp.get(url, status=200)
        self.assertTrue('Search groups' in res.body)
        self.assertTrue('avengers' in res.body)
        self.assertTrue('all-star' in res.body)



if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsGroupsFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)