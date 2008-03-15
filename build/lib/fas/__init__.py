from fas import release
__version__ = release.VERSION

class FASError(Exception):
    '''FAS Error'''
    pass

class ApplyError(FASError):
    '''Raised when a user could not apply to a group'''
    pass

class ApproveError(FASError):
    '''Raised when a user could not be approved in a group'''
    pass

class SponsorError(FASError):
    '''Raised when a user could not be sponsored in a group'''
    pass

class UpgradeError(FASError):
    '''Raised when a user could not be upgraded in a group'''
    pass

class DowngradeError(FASError):
    '''Raised when a user could not be downgraded in a group'''
    pass

class RemoveError(FASError):
    '''Raised when a user could not be removed from a group'''
    pass
