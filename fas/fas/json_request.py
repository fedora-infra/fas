import turbogears
from turbogears import controllers, expose, identity 

from fas.auth import *

class JsonRequest(controllers.Controller):
    def __init__(self):
        """Create a JsonRequest Controller."""

    @expose("json")
    def index(self):
        """Return a help message"""
        return dict(help='This is a json interface')

