RESTful API
===========

Features
~~~~~~~~

People API
^^^^^^^^^^
nlnalnalanaln

* Get list of people
* Get person info
* Edit person's profile

Groups API
^^^^^^^^^^
* Get list of groups
* Get group's info
* Edit group

Architecture
~~~~~~~~~~~~

Add REST's method
~~~~~~~~~~~~~~~~~

Init Metadata's object:

.. code-block:: python

    from api import Metadata

    metadata = Metadata(<my_api_name_space>)


Add the route to your method in ``fas/__init__.py``:

.. code-block:: python

    config.add_route('api-people', '/api/person/{username}')

Write your class from ``fas/api/people.py``:

.. code-block:: python

    class PeopleAPI(object):

    def __init__(self, request):
        self.request = request

        # Init Metadata object
        self.data = MetaData('People')

        # Define a member variable to manage notification
        self.notify = self.request.registry.notify

        # Define a URL's parameters validators
        self.params = self.request.param_validator
        self.perm = None

        self.request.param_validator.add_optional('limit')
        self.request.param_validator.add_optional('page')
        self.request.param_validator.add_optional('status')

        # Send notification to any API's request
        # This notification will be catched up by event's listener which 
        # will check passing URL's parameters and the API token.
        self.notify(ApiRequest(self.request, self.data, self.perm))

    @view_config(route_name='my_route_name', renderer='json', request_method=<HTTP_request>)
    def person_info(self):
        """ Provides people list.

        .. example::
           example REST call
           example REAT call's output
        """
        if self.apikey.validate():
            # put your code here
            people = provider.get_people(limit=self.

        return self.data.get_metadata()
