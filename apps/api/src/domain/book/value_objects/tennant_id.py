import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Tenant ID is required")

    @staticmethod
    def generate(user_id: str, book_id: str) -> "TenantId":
        user_hex = uuid.UUID(user_id).hex
        book_hex = uuid.UUID(book_id).hex
        encoded = user_hex + book_hex
        return TenantId(encoded)

    def get_user_id(self) -> str:
        decoded = self.value[:32]
        return str(uuid.UUID(decoded))

    def get_book_id(self) -> str:
        decoded = self.value[32:]
        return str(uuid.UUID(decoded))
