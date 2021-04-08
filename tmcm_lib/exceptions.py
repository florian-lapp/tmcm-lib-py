import abc

class Exception(Exception, abc.ABC) :
    """Generic exception."""
    pass

class InternalException(Exception) :
    """
    Exception that indicates an internal error.

    This exception should never occur and therefore is not needed to catch.
    """
    pass

class AddressException(Exception) :
    """Exception that indicates that an address is wrong."""
    pass

class IdentityException(Exception) :
    """Exception that indicates that an identity is wrong."""
    pass

class ChecksumException(Exception, abc.ABC) :
    """
    Exception that indicates that the checksum of a request or a reply is wrong.

    The reason for this exception is an unstable communication from the host to the module or from
    the module to the host.
    """
    pass

class ChecksumRequestException(ChecksumException) :
    """
    Exception that indicates that the checksum of a request is wrong.

    The reason for this exception is an unstable communication from the host to the module.
    """
    pass

class ChecksumReplyException(Exception) :
    """
    Exception that indicates that the checksum of a reply is wrong.

    The reason for this exception is an unstable communication from the module to the host.
    """
    pass

class StateException(Exception) :
    """
    Exception that indicates that a method was invoked in a state when it is not allowed to be
    invoked.
    """
    pass

del abc