# -*- coding: utf-8 -*-
#
# Copyright © 2007-2008  Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Red Hat Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#

'''
JSON Helper functions.  Most JSON code directly related to classes is
implemented via the __json__() methods in model.py.  These methods define
methods of transforming a class into json for a few common types.
'''
# A JSON-based API(view) for your app.
# Most rules would look like:
# @jsonify.when("isinstance(obj, YourClass)")
# def jsonify_yourclass(obj):
#     return [obj.val1, obj.val2]
# @jsonify can convert your objects to following types:
# lists, dicts, numbers and strings

import sqlalchemy
from turbojson.jsonify import jsonify

class SABase(object):
    '''Base class for SQLAlchemy mapped objects.

    This base class makes sure we have a __json__() method on each SQLAlchemy
    mapped object that knows how to::

    1) return json for the object.
    2) Can selectively add tables pulled in from the table to the data we're
       returning.
    '''
    # pylint: disable-msg=R0903
    def __json__(self):
        '''Transform any SA mapped class into json.

        This method takes an SA mapped class and turns the "normal" python
        attributes into json.  The properties (from properties in the mapper)
        are also included if they have an entry in jsonProps.  You make
        use of this by setting jsonProps in the controller.

        Example controller::
          john = model.Person.get_by(name='John')
          # Person has a property, addresses, linking it to an Address class.
          # Address has a property, phone_nums, linking it to a Phone class.
          john.jsonProps = {'Person': ['addresses'],
                  'Address': ['phone_nums']}
          return dict(person=john)

        jsonProps is a dict that maps class names to lists of properties you
        want to output.  This allows you to selectively pick properties you
        are interested in for one class but not another.  You are responsible
        for avoiding loops.  ie: *don't* do this::
            john.jsonProps = {'Person': ['addresses'], 'Address': ['people']}
        '''
        props = {}
        # pylint: disable-msg=E1101
        if 'jsonProps' in self.__dict__ \
                and self.jsonProps.has_key(self.__class__.__name__):
            propList = self.jsonProps[self.__class__.__name__]
        else:
            propList = {}
        # pylint: enable-msg=E1101
       
        # Load all the columns from the table
        for key in self.mapper.props.keys(): # pylint: disable-msg=E1101
            if isinstance(self.mapper.props[key], # pylint: disable-msg=E1101
                    sqlalchemy.orm.properties.ColumnProperty):
                props[key] = getattr(self, key)
        # Load things that are explicitly listed
        for field in propList:
            props[field] = getattr(self, field)
            try:
                # pylint: disable-msg=E1101
                props[field].jsonProps = self.jsonProps
            except AttributeError: # pylint: disable-msg=W0704
                # Certain types of objects are terminal and won't allow setting
                # jsonProps
                pass
        return props

@jsonify.when("isinstance(obj, sqlalchemy.orm.query.Query)" \
        " or isinstance(obj, sqlalchemy.ext.selectresults.SelectResults)")
def jsonify_sa_select_results(obj):
    '''Transform selectresults into lists.
    
    The one special thing is that we bind the special jsonProps into each
    descendent.  This allows us to specify a jsonProps on the toplevel
    query result and it will pass to all of its children.
    '''
    if 'jsonProps' in obj.__dict__:
        for element in obj:
            element.jsonProps = obj.jsonProps
    return list(obj)

@jsonify.when("isinstance(obj, sqlalchemy.orm.attributes.InstrumentedList)")
def jsonify_salist(obj):
    '''Transform SQLAlchemy InstrumentedLists into json.
    
    The one special thing is that we bind the special jsonProps into each
    descendent.  This allows us to specify a jsonProps on the toplevel
    query result and it will pass to all of its children.
    '''
    if 'jsonProps' in obj.__dict__:
        for element in obj:
            element.jsonProps = obj.jsonProps
    return [jsonify(element) for element in  obj]
