"""
Helper class to manage creation of Python native datatypes for consumption by SkinToneDetectionSessionSerializer.
"""
from enum import Enum
from . import models
from . import response_helper


class SkinToneSessionState(Enum):
    NEW = 1
    IN_PROGRESS = 2
    COMPLETE = 3


class SkinToneDetectionSessionHelper:

    @staticmethod
    def create(state: SkinToneSessionState, user: models.User) -> models.SkinToneDetectionSession:
        return models.SkinToneDetectionSession(state=str(state.name), user=user)

    @staticmethod
    def create_response(session_id: str):
        response_message = response_helper.create_response_message("New skin tone detection session created")
        response_message["session_id"] = session_id
        return response_message
