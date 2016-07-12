import unittest

from tests import BaseTest


class ViewsRegisterFunctionalTests(BaseTest):
    def test_root(self):
        res = self.testapp.get('/register', status=200)
        exp_str = '<h1>Create your Fedora Project Account</h1>'
        self.assertTrue(exp_str in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ViewsRegisterFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
