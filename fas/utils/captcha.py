# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Ralph Bean.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Authors:  Ralph Bean <rbean@redhat.com>
#           Xavier Lamien <laxathom@fedoraproject.org>

import base64
import cryptography.fernet
import random
import six

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from . import Config


class Captcha(Config):
    """
    Generate a captcha math equation and validate its value
    from given solution.

    Inherit from `fas.utils.Config`
    """
    def __init__(self, config=None):
        #TODO: Manage captcha configs value from initialization.
            self.font_path = self.get('captcha.font.path')
            self.font_size = int(self.get('captcha.font.size'))
            self.font_color = self.get('captcha.font.color')
            self.bg_color = self.get('captcha.background.color')
            self.padding = int(self.get('captcha.font.padding'))
            self.image_width = self.get('captcha.image.width')
            self.image_height = self.get('captcha.image.height')
            self.secret = self.get('captcha.secret')
            self.ttl = self.get('captcha.ttl')
            self.encoding = self.get('captcha.encoding')

    def __math_generator__(self, plainkey=None):
        """ Generate a math equation from a given plainkey
        and return its expected value.

        :param plainkey:
            The plainkey to pass as input. If `None`, generate a random one.
        :return:
            Math equation and its related solution.
        :rtype: tuple(string, integer)
        """
        if not plainkey:
            x = random.randint(1, 100)
            y = random.randint(1, 100)
            plainkey = "%i + %i =" % (x, y)

        tokens = plainkey.split()
        if not len(tokens) == 4:
            raise ValueError("%s is an invalid plainkey" % plainkey)

        if tokens[1] != '+' or tokens[3] != '=':
            raise ValueError("%s is an invalid plainkey" % plainkey)

        x, y = int(tokens[0]), int(tokens[2])

        value = six.text_type(x + y)
        return plainkey, int(value)

    def __jpeg_generator__(self, plainkey):
        """
        Generate a JPEG data from a given keys combo

        :param plainkey:
            The keys combo to draw in JPEG data.
        :type plainkey: string
        :param config:
            The config object to retrieve configs to build the JPEG data.
        :return:
            Generated JPEG data.
        :rtype: `Image.paste`
        """
        image_size = image_width, image_height = (
            int(self.image_width),
            int(self.image_height),
        )

        img = Image.new('RGB', image_size)

        img.paste(self.bg_color)

        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            return

        width, height = font.getsize(plainkey)

        draw = ImageDraw.Draw(img)
        position = (
            random.randint(
                self.padding, (image_width - width - self.padding)
                ),
            random.randint(
                self.padding, (image_height - height - self.padding))
                )
        draw.text(position, plainkey, font=font, fill=self.font_color)

        return img

    def __encrypt__(self, plaintext):
        """
        Encrypt given captcha text and return encrypted data.

        :param plaintext:
            Text to encrypt
        :type plaintext: string
        :return:
            Encrypted `plaintext`
        :rtype: string
        """
        engine = cryptography.fernet.Fernet(self.secret)
        ciphertext = engine.encrypt(plaintext.encode(self.encoding))
        ciphertext = base64.urlsafe_b64encode(ciphertext)

        return ciphertext

    def __decrypt__(self, ciphertext):
        """
        Decrypt captcha text from given cipher key and
        return it.

        :param cipherkey:
            A cipher key from a generated captcha data
        :type cipherkey: string
        :return: decrypted captcha data
        """
        engine = cryptography.fernet.Fernet(self.secret)

        if isinstance(ciphertext, six.text_type):
            ciphertext = ciphertext.encode(self.encoding)

        ciphertext = base64.urlsafe_b64decode(ciphertext)
        plaintext = engine.decrypt(ciphertext, ttl=int(self.ttl))

        return plaintext.decode(self.encoding)

    def generate_key(self):
        """
        Generate Captcha key from auto-generated math equation and solution

        :return: generated cipher key
        :rtype: string
        """
        plainkey, value = self.__math_generator__()
        cipherkey = self.__encrypt__(plainkey)
        #url = request.route_url('captcha-image', cipherkey=cipherkey)
        return cipherkey

    def get_image(self, cipherkey):
        """
        Retrieve Captcha image from given request

        :param cipherkey:
            A given cipherkey from `Captcha.generate_key`
        :type cipherkey: string
        :return:
            Generated image from given cipherkey
        :rtype: `Image.paste`
        """
        return self.__jpeg_generator__(self.__decrypt__(cipherkey))

    def validate(self, cipherkey, value):
        """
        Validate captcha value from given key and math solution

        :param cipherkey:
            Generated chiper key from captcha input
        :type chiperkey: String
        :param value:
            Captcha value to validate against given `cipherkey`
        :return: True if `value` is correct, False otherwise.
        :rtype: boolean
        """
        try:
            plainkey = self.__decrypt__(cipherkey)
        except cryptography.fernet.InvalidToken:
            return False

        _, expected_value = self.__math_generator__(plainkey)

        return value == expected_value
