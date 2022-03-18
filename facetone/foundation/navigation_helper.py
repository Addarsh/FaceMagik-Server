"""
Helper class to fetch navigation instruction based on scene conditions.
"""

from enum import Enum
from facemagik.skintone import SceneBrightnessAndDirection
from facemagik.common import SceneBrightness, LightDirection


class NavigationInstruction(Enum):
    # User is opposite to the direction of light, turn around to face light.
    TURN_AROUND_180 = 1
    # User is facing light but it's too bright.
    WALK_BACKWARDS_SLOWLY = 2
    # User is facing light but there is not enough light falling on them.
    LESS_BRIGHTNESS_WALK_FORWARD_SLOWLY = 3
    # User is in neutral lighting conditions and should stop moving.
    NEUTRAL_LIGHTING_STOP = 4
    # User is not facing light but can turn left to eventually face light.
    TURN_LEFT_TO_FACE_LIGHT = 5
    # User is not facing light but can turn right to eventually face light.
    TURN_RIGHT_TO_FACE_LIGHT = 6
    # User is 90 degrees from direction of light and needs to turn left.
    TURN_LEFT_90 = 7
    # User is 90 degrees from direction of light and needs to turn right.
    TURN_RIGHT_90 = 8


class NavigationHelper:

    @staticmethod
    def get_instruction(scene_brightness_and_direction: SceneBrightnessAndDirection) -> NavigationInstruction:
        scene_brightness: SceneBrightness = scene_brightness_and_direction.scene_brightness()
        primary_light_direction: LightDirection = scene_brightness_and_direction.primary_light_direction

        if primary_light_direction == LightDirection.CENTER or primary_light_direction == LightDirection.CENTER_LEFT \
                or primary_light_direction == LightDirection.CENTER_RIGHT or primary_light_direction == \
                LightDirection.LEFT_CENTER_RIGHT or primary_light_direction == LightDirection.RIGHT_CENTER_LEFT:
            if scene_brightness == SceneBrightness.DARK_SHADOW:
                # User is opposite to the direction of light.
                return NavigationInstruction.TURN_AROUND_180
            elif scene_brightness == SceneBrightness.TOO_BRIGHT:
                # User is facing light but it's too bright.
                return NavigationInstruction.WALK_BACKWARDS_SLOWLY
            elif scene_brightness == SceneBrightness.SOFT_SHADOW:
                # User is facing light but there is not enough light falling on them.
                return NavigationInstruction.LESS_BRIGHTNESS_WALK_FORWARD_SLOWLY
            elif scene_brightness == SceneBrightness.NEUTRAL_LIGHTING:
                # User is in neutral lighting conditions and should stop moving.
                return NavigationInstruction.NEUTRAL_LIGHTING_STOP
            raise ValueError("Unsupported Scene brightness: " + scene_brightness)
        elif primary_light_direction == LightDirection.RIGHT_CENTER:
            # User is not facing light but can turn left to eventually face light.
            return NavigationInstruction.TURN_LEFT_TO_FACE_LIGHT
        elif primary_light_direction == LightDirection.LEFT_CENTER:
            # User is not facing light but can turn right to eventually face light.
            return NavigationInstruction.TURN_RIGHT_TO_FACE_LIGHT
        elif primary_light_direction == LightDirection.LEFT_TO_RIGHT:
            return NavigationInstruction.TURN_RIGHT_90
        elif primary_light_direction == LightDirection.RIGHT_TO_LEFT:
            return NavigationInstruction.TURN_LEFT_90

        raise ValueError("Unsupported Scene Light direction: ", primary_light_direction)
