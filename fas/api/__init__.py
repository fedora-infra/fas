# -*- coding: utf-8 -*-

from pyramid.view import view_config

import datetime


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


class ParamsValidator:

    def __init__(self, request):
        self.request = request
        self.params = [u'apikey']
        self.apikey = ''
        self.pageoffset = 0
        self.optional_params = []
        self.msg = ()

    def __set_msg__(self, name, text=''):
        self.msg = (name, text)

    def add_optional(self, optional):
        """ Add optional parameter to validate.

        :args optional: string, requested optional parameter.
        """
        self.optional_params.append(unicode(optional))

    def add_param(self, params):
        """ Add mandatory parameter to validate.

        :arg params: string, requested madatory parameter.
        """
        self.params.append(unicode(params))

    def is_valid(self):
        """ Check if request's parameters are valid.

        :returns: True if all given parameters are valid. False otherwise.
        """
        if self.optional_params:
            for p in self.optional_params:
                self.params.append(p)

        if self.request.params:
            for key, value in self.request.params.iteritems():
                if key not in self.params:
                    self.__set_msg__('Parameter Error.',
                                    'Invalid parameter: %r' % str(key))
                    return False
                else:
                    if not value and (key not in self.optional_params):
                        if key == 'apikey':
                            self.request.reponse.status = '401 Unauthorized'
                            self.__set_msg__('Access denied.',
                                            "Required API key is missing.")
                        else:
                            self.__set_msg__('Invalid parameters', '')
                        return False
                    if key == 'apikey':
                        self.apikey = value
                    elif key == 'pageoffset':
                        self.pageoffset = int(value)
            return True
        else:
            self.request.reponse.status = '400 bad request'
            self.__set_msg__('Parameter error.', 'No parameter(s) found.')
        return False

    def set_params(self, params):
        self.params.append(params)

    def get_apikey(self):
        """ Get API key value from request parameter. """
        return self.apikey

    def get_pageoffset(self):
        """ Get page index for pagination. """
        return self.pageoffset

    def get_msg(self):
        """ Get error messages from a validation check.

        :returns: tuple object of error message if is_valid() is False,
                  None otherwise.
        """
        return self.msg


class MetaData():

    def __init__(self, name=None):
        self.data = {}
        #self.metadata[name + 'Result'] = {}
        self.name = name
        self.datetime = datetime.datetime
        self.strftime = '%Y-%m-%dT%H:%M:%S%Z'
        self.timestamp = self.datetime.utcnow().strftime(self.strftime)

    def set_error_msg(self, name='', text=''):
        """ Set error message into metadata's dict().

        :arg name: String, error name.
        :arg text: String, text that describe the error.
        """
        self.data['Error'] = {}
        self.data['Error']['Name'] = name
        self.data['Error']['Text'] = text

    def set_data(self, data):
        """ Add data info to metadata dict.

        :arg data: dict or list of dict's object.
        """
        self.data[self.name] = data

    def get_metadata(self):
        """ get metadata from Request's object.

            :returns: Dict object of metadata from given parameters.
        """
        self.data['StartTimeStamp'] = self.timestamp
        self.data['EndTimeStamp'] = self.datetime.utcnow().strftime(self.strftime)

        return self.data


@view_config(route_name='api_home', renderer='/api_home.xhtml')
def api_home(request):
    return {}

