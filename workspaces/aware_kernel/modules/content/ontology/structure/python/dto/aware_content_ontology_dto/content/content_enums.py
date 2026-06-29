from __future__ import annotations

# Standard
from enum import Enum


class ContentSource(Enum):
    agent = "agent"
    event = "event"
    instruction = "instruction"
    memory = "memory"
    tool = "tool"
    user = "user"


class ModalityType(Enum):
    audio = "audio"
    image = "image"
    text = "text"
    video = "video"
