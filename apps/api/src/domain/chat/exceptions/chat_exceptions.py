class ChatError(Exception):
    pass


class ChatNotFoundError(ChatError):
    def __init__(self, message: str = "Chat not found") -> None:
        self.message = message
        super().__init__(self.message)


class ChatAlreadyExistsError(ChatError):
    def __init__(self, message: str = "Chat already exists") -> None:
        self.message = message
        super().__init__(self.message)


class ChatValidationError(ChatError):
    def __init__(self, message: str = "Chat validation failed") -> None:
        self.message = message
        super().__init__(self.message)


class ChatPermissionDeniedError(ChatError):
    """CR-3: 認証ユーザーが対象 Chat の所有者でない場合."""

    def __init__(self, message: str = "Chat permission denied") -> None:
        self.message = message
        super().__init__(self.message)
