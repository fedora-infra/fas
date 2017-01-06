import unittest
import mock

from fas.models.people import People
from tests import BaseTest
from wtforms import (
    Form,
    IntegerField,
    HiddenField
)


class MockCaptchaForm(Form):
    """ Form to validate captcha. """
    key = HiddenField('key')
    captcha = IntegerField('Captcha')


class MockSignLicenseForm(Form):
    """ Form to validate signed license agreement from registered people."""
    license = 'License Agreement'
    people = 1
    signed = True


class ViewsRegisterFunctionalTests(BaseTest):
    def test_register_get(self):
        res = self.testapp.get('/register', status=200)
        exp_str = '<h1>Create your Fedora Project Account</h1>'
        self.assertTrue(exp_str in res.body)

    @mock.patch('fas.views.register.CaptchaForm')
    def test_register_valid(self, mock_captcha):
        mock_captcha = MockCaptchaForm()

        form = {'form.register': True,
                'username': 'skrzepto',
                'fullname': 'skrzepto',
                'password_confirm': 'test12',
                'password': 'test12',
                'email': 'skrzepto@test.com'}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        redirect_res = self.testapp.post('/register', form, headers, status=302)
        res = redirect_res.follow()
        # redirecting to /people means a succesful account creation
        expected = 'http://localhost/people; you should be redirected automatically.'
        self.assertTrue(expected in res.body)

    @mock.patch('fas.views.register.CaptchaForm')
    def test_register_same_email(self, mock_captcha):
        mock_captcha = MockCaptchaForm()

        form = {'form.register': True,
                'username': 'skrzepto',
                'fullname': 'skrzepto',
                'password_confirm': 'test12',
                'password': 'test12',
                'email': 'skrzepto@test.com'}

        form2 = {'form.register': True,
                 'username': 'skrzepto_2',
                 'fullname': 'skrzepto_2',
                 'password_confirm': 'test12',
                 'password': 'test12',
                 'email': 'skrzepto@test.com'}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        redirect_res = self.testapp.post('/register', form, headers, status=302)
        res = redirect_res.follow()
        # redirecting to /people means a succesful account creation
        expected = 'http://localhost/people; you should be redirected automatically.'
        self.assertTrue(expected in res.body)

        expected_str = '<li><label for="email">Email</label>: ' \
                       'skrzepto@test.com exists already!</li>'
        res = self.testapp.post('/register', form2, headers, status=200)
        # redirecting to /people means a succesful account creation
        self.assertTrue(expected_str in res.body)

    @unittest.skip("Currently failing when two accounts created with same data, "
                   "Expect to have second registration to say "
                   "account already registered")
    @mock.patch('fas.views.register.CaptchaForm')
    def test_register_empty_irc(self, mock_captcha):
        mock_captcha = MockCaptchaForm()

        form = {'form.register': True,
                'username': 'skrzepto',
                'fullname': 'skrzepto',
                'password_confirm': 'test12',
                'password': 'test12',
                'email': 'skrzepto@test.com'}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        redirect_res = self.testapp.post('/register', form, headers, status=302)
        res = redirect_res.follow()
        # redirecting to /people means a succesful account creation
        self.assertTrue('The resource was found at /people' in res.body)

        res = self.testapp.post('/register', form, headers, status=200)
        # redirecting to /people means a succesful account creation
        self.assertTrue('' in res.body)

    @unittest.skip("Currently failing need to look into how the account is confirmed again")
    @mock.patch('fas.views.register.CaptchaForm')
    def test_create_and_confirm_account(self, mock_captcha):
        mock_captcha = MockCaptchaForm()

        form = {'form.register': True,
                'username': 'skrzepto',
                'fullname': 'skrzepto',
                'password_confirm': 'test12',
                'password': 'test12',
                'email': 'skrzepto@test.com'}

        headers = [('User-Agent', 'Python/Unittests'), ]
        self.testapp.extra_environ.update(dict(REMOTE_ADDR='127.0.0.1'))
        redirect_res = self.testapp.post('/register', form, headers)
        res = redirect_res.follow()
        # redirecting to /people means a succesful account creation
        expected = 'http://localhost/people; you should be redirected automatically.'
        self.assertTrue(expected in res.body)

        person = self.DBSession.query(
            People
        ).filter(
            People.username == 'skrzepto'
        ).first()

        form = {'username': 'skrzepto',
                'token': person.password_token}
        url = '/register/confirm/{}/{}'.format(form['username'], form['token'])
        res = self.testapp.post(url, form, headers, status=302)
        # if succesfully confirmed account redirect to profile page
        self.assertTrue('/people/profile/{}'.format(person.id) in res.body)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        ViewsRegisterFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
