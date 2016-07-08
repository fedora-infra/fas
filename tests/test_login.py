import unittest
import transaction
from pyramid import testing
from fas.models import DBSession
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


class FunctionalTests(BaseTest):
    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue('<title>The Fedora Project Account System</title>' in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)