from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lectio.user import User


class FilterEnum(IntEnum):
    OWN = -10
    UNREAD = -40
    FLAG = -50
    REMOVED = -60
    NEWEST = -70
    SENT = -80


@dataclass
class MessageInfo:
    title: str
    timestamp: str
    creator: dict[str, str]
    to: str
    threadid: int


@dataclass
class Message:
    user: "User"
    timestamp: datetime
    title: str
    content: str
    replies: list["Message"]
