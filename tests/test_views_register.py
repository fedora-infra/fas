import unittest
import mock
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
    @mock.patch('fas.views.register.SignLicenseForm')
    def test_register_valid(self, mock_captcha, mock_sign_license):
        '''
        I need to mock out
        from fas.forms.captcha import CaptchaForm
        to give the same question everytime

        '''
        mock_captcha = MockCaptchaForm()
        mock_sign_license = MockSignLicenseForm()

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


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ViewsRegisterFunctionalTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
