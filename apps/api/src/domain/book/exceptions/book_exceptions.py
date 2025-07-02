class BookDomainException(Exception):  # noqa: N818
    """Bookドメインに関連する例外の基底クラス"""


class BookNotFoundException(BookDomainException):
    """要求された書籍が見つからなかった場合の例外"""

    def __init__(self, book_id: str) -> None:
        self.book_id = book_id
        super().__init__(f"ID {book_id} の書籍が見つかりません")


class BookAlreadyStartedException(BookDomainException):
    """既に開始されている書籍を再度開始しようとした場合の例外"""

    def __init__(self) -> None:
        super().__init__("この書籍は既に読書開始状態です")


class BookAlreadyCompletedException(BookDomainException):
    """既に完了している書籍に対して操作を行おうとした場合の例外"""

    def __init__(self) -> None:
        super().__init__("この書籍は既に読了済みです")


class BookPermissionDeniedException(BookDomainException):
    """ユーザーが書籍に対するアクセス権を持っていない場合の例外"""

    def __init__(self) -> None:
        super().__init__("この書籍へのアクセス権限がありません")


class BookFileNotFoundException(BookDomainException):
    """書籍ファイルが見つからない場合の例外"""

    def __init__(self) -> None:
        super().__init__("この書籍のファイルが見つかりません")
