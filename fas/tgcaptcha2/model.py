from datetime import datetime
import calendar
import cPickle


class Captcha(object):
    """Pertinent data about a Captcha.
    
    Exposed properties are:
    plaintext: (read/write) a string representing the text of the captcha 
                (i.e. what is it supposed to say)
    created: (read only) the UTC date when the captcha was created. This 
                data is updated when the plaintext property is updated.
                
    Exposed methods:
    serialize(): returns a binary representation of the object
    deseralize(obj): creates a Captcha object given the output of the
                serialize() method. This is a classmethod.
    """

    _plaintext = None
    _created = None  # stored as UTC

    def __init__(self, plaintext=''):
        super(Captcha, self).__init__()
        self.plaintext = plaintext
        self.label = None

    def get_plaintext(self):
        return self._plaintext

    def set_plaintext(self, text):
        self._plaintext = text
        self._created =  datetime.utcnow()

    plaintext = property(get_plaintext, set_plaintext)
    # def get_created(self):
    #     return self._created

    c = lambda s: s._created

    created = property(lambda s: s._created)

    def serialize(self):
        """Get a serialized binary representation of the object."""
        # Serializing to a tuple containing the data elements instead of 
        # just pickling the object is being done because the tuple 
        # pickle is much smaller than the pickled object itself.
        secs = int(calendar.timegm(self.created.utctimetuple()))
        t = (self.plaintext, secs, self.label)
        return cPickle.dumps(t, cPickle.HIGHEST_PROTOCOL)

    def deserialize(cls, serialized_obj):
        "Create a new Captcha object given output from the serialize method."
        t = cPickle.loads(serialized_obj)
        scp = cls()
        scp._plaintext = t[0]
        scp._created = datetime.utcfromtimestamp(t[1])
        scp.label = t[2]
        return scp
    deserialize = classmethod(deserialize)
