from datetime import datetime
from turbogears.database import PackageHub
from sqlobject import *
from turbogears import identity 

hub = PackageHub("fas")
__connection__ = hub

# class YourDataClass(SQLObject):
#     pass

# identity models.
class Visit(SQLObject):
    class sqlmeta:
        table = "visit"

    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    created = DateTimeCol(default=datetime.now)
    expiry = DateTimeCol()

    def lookup_visit(cls, visit_key):
        try:
            return cls.by_visit_key(visit_key)
        except SQLObjectNotFound:
            return None
    lookup_visit = classmethod(lookup_visit)

class VisitIdentity(SQLObject):
    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    user_id = IntCol()

