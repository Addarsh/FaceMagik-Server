"""
Helper class to manage creation of Python native datatypes for consumption by SkinToneDetectionSessionSerializer.
"""
from enum import Enum
from . import models
from . import response_helper
from .navigation_helper import NavigationInstruction


class SkinToneSessionState(Enum):
    NEW = 1
    IN_PROGRESS = 2
    COMPLETE = 3


class SkinToneDetectionSessionHelper:
    SESSION_ID_KEY = "session_id"
    NAVIGATION_INSTRUCTION_KEY = "navigation_instruction"

    @staticmethod
    def create(state: SkinToneSessionState, user: models.User) -> models.SkinToneDetectionSession:
        return models.SkinToneDetectionSession(state=str(state.name), user=user)

    @staticmethod
    def create_response(session_id: str):
        response_message = response_helper.create_response_message("New skin tone detection session created")
        response_message[SkinToneDetectionSessionHelper.SESSION_ID_KEY] = session_id
        return response_message

    @staticmethod
    def create_navigation_response(session_id: str, navigation_instruction: NavigationInstruction):
        response_message = response_helper.create_response_message("Computed scene lighting conditions")
        response_message[SkinToneDetectionSessionHelper.SESSION_ID_KEY] = session_id
        response_message[SkinToneDetectionSessionHelper.NAVIGATION_INSTRUCTION_KEY] = str(navigation_instruction.name)
        return response_message
