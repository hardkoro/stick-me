"""Models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """User."""

    id: int
    name: str


@dataclass(frozen=True)
class Conversation:
    """Conversation."""

    user: User
    chat_id: int

    @property
    def username(self) -> str:
        """Get username."""
        return self.user.name

    @property
    def user_id(self) -> int:
        """Get user id."""
        return self.user.id


@dataclass
class Sticker:
    """Sticker."""

    file_id: str
    emoji: str
    content: bytes | None = None
