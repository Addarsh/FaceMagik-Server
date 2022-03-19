"""
Helper class to manage creation of Python native datatypes for consumption by SkinToneDetectionSessionSerializer.
"""
import json
from enum import Enum
from . import models
from . import response_helper
from facemagik.skintone import SceneBrightnessAndDirection, SkinTone
from .navigation_helper import NavigationInstruction


class SessionState(Enum):
    NEW = 1
    IN_PROGRESS = 2
    COMPLETE = 3


class SessionModelsManager:

    @staticmethod
    def create_session(state: SessionState, user: models.User) -> models.SkinToneDetectionSession:
        return models.SkinToneDetectionSession(state=str(state.name), user=user)

    @staticmethod
    def update_session_state(session: models.SkinToneDetectionSession, state: SessionState) -> \
            models.SkinToneDetectionSession:
        session.state = str(state.name)
        return session

    @staticmethod
    def is_state_complete(session: models.SkinToneDetectionSession) -> bool:
        return session.state == str(SessionState.COMPLETE.name)

    @staticmethod
    def create_image(session: models.SkinToneDetectionSession, scene_brightness_and_direction:
    SceneBrightnessAndDirection, navigation_instruction: NavigationInstruction) -> \
            models.SkinToneDetectionImage:
        return models.SkinToneDetectionImage(skin_tone_detection_session=session,
                                             scene_brightness_value=scene_brightness_and_direction.scene_brightness_value,
                                             scene_brightness_description=str(
                                                 scene_brightness_and_direction.scene_brightness().name),
                                             primary_light_direction=str(
                                                 scene_brightness_and_direction.primary_light_direction.name),
                                             navigation_instruction=str(navigation_instruction.name))

    @staticmethod
    def create_skin_tones(skin_tones: [SkinTone], image: models.SkinToneDetectionImage) -> \
            [models.SkinTone]:
        return [models.SkinTone(skin_tone_detection_image=image, rgb_values=json.dumps(skin_tone.rgb),
                                color_profile=skin_tone.profile,
                                percentage_of_face_mask=skin_tone.percent_of_face_mask)
                for
                skin_tone in
                skin_tones]


class SessionResponseHelper:
    SESSION_ID_KEY = "session_id"
    NAVIGATION_INSTRUCTION_KEY = "navigation_instruction"
    SKIN_TONES = "skin_tones"
    RGB = "rgb"
    PERCENT = "percent"

    @staticmethod
    def new_session_created_response(session_id: str):
        response_message = response_helper.create_response_message("New skin tone detection session created")
        response_message[SessionResponseHelper.SESSION_ID_KEY] = session_id
        return response_message

    @staticmethod
    def create_navigation_and_skin_tones_response(session_id: str, navigation_instruction: NavigationInstruction,
                                                  skin_tones: [SkinTone]):
        response_message = response_helper.create_response_message("Computed scene lighting conditions")
        response_message[SessionResponseHelper.SESSION_ID_KEY] = session_id
        response_message[SessionResponseHelper.NAVIGATION_INSTRUCTION_KEY] = str(navigation_instruction.name)
        if len(skin_tones) > 0:
            response_message[SessionResponseHelper.SKIN_TONES] = [{SessionResponseHelper.RGB: st.rgb,
                                                                  SessionResponseHelper.PERCENT:
                                                                      st.percent_of_face_mask} for st
                                                                 in
                                                                 skin_tones]
        return response_message

    @staticmethod
    def session_ended_response(session_id: str):
        response_message = response_helper.create_response_message("Session ended")
        response_message[SessionResponseHelper.SESSION_ID_KEY] = session_id
        return response_message
