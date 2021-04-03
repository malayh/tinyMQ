

class InitFailed(Exception):
    """
    Raised when initilizing connection and ConnStatus != Status.CON_OPEN
    """
    pass

class WrongAck(Exception):
    """
    Raise when ACK.id is not equal to the id you send
    """
    pass

class DeadConnectionUsed(Exception):
    """
    Raised when client tried to send or recv from uninitialized connections
    """
    pass
    