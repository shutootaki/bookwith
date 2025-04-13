class MessageDomainException(Exception):
    pass


class MessageNotFoundException(MessageDomainException):
    def __init__(self, message_id: str) -> None:
        self.message_id = message_id
        super().__init__(f"ID {message_id} のメッセージが見つかりません")


class MessageAlreadyDeletedException(MessageDomainException):
    def __init__(self) -> None:
        super().__init__("このメッセージは既に削除されています")


class MessageDeliveryFailedException(MessageDomainException):
    def __init__(self) -> None:
        super().__init__("メッセージの配信に失敗しました")


class MessagePermissionDeniedException(MessageDomainException):
    def __init__(self) -> None:
        super().__init__("このメッセージへのアクセス権限がありません")
