# -*- coding: utf-8 -*-

from cryptacular.bcrypt import BCRYPTPasswordManager


class PasswordManager():

    def __init__(self):
        self.manager = BCRYPTPasswordManager()

    def generate_password(self, password):
        """ Generate a password and return it."""
        return self.manager.encode(password)

    def is_valid_password(self, registered, current):
        """ Check password against registered one"""
        if self.manager.match(registered):
            if self.manager.check(registered, current):
                return True
        return False
