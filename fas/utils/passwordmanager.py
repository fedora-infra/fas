# -*- coding: utf-8 -*-
#
# Copyright © 2014 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

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
