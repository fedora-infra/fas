class test:
    __var = 'Uninitalized'

    def __getattr__(self, attr):
        return self.__getattr__(attr)

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value

    @classmethod
    def start(cls):
        self = cls()
        return self

p = test.start()
p.var='first'
t = test.start()
t.var='second'

print p.var
print t.var
