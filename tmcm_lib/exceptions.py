import abc

class Exception(Exception, abc.ABC) :
    """Generic exception."""
    pass

class ExceptionInternal(Exception) :
    """
    Exception that indicates an internal error.

    This exception should never occur and therefore is not needed to catch.
    """
    pass

class ExceptionIdentity(Exception) :
    """Exception that indicates that an identity is wrong."""

class ExceptionChecksum(Exception, abc.ABC) :
    """
    Exception that indicates that the checksum of a request or a reply is wrong.

    The reason for this exception is an unstable communication from the host to the module or from
    the module to the host.
    """
    pass

class ExceptionChecksumRequest(ExceptionChecksum) :
    """
    Exception that indicates that the checksum of a request is wrong.

    The reason for this exception is an unstable communication from the host to the module.
    """
    pass

class ExceptionChecksumReply(Exception) :
    """
    Exception that indicates that the checksum of a reply is wrong.

    The reason for this exception is an unstable communication from the module to the host.
    """
    pass

class ExceptionState(Exception) :
    """
    Exception that indicates that a method was invoked in a state when it is not allowed to be
    invoked.
    """
    pass