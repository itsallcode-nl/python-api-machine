class ClientError(RuntimeError):
    pass


class InvalidMessage(ClientError):
    pass


class ValidationError(ClientError):
    pass


class OperationDoesNotExist(InvalidMessage):
    pass
