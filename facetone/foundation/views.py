import numpy as np

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import User, SkinToneDetectionSession
from .serializers import SessionSerializer, UserIdSerializer, SessionIdSerializer
from .response_helper import create_response_message, create_response_message_with_error_code
from .session_models_manager import SessionModelsManager, SessionState, SessionResponseHelper
from facemagik.skintone import SkinToneAnalyzer, SkinDetectionConfig, TeethNotVisibleException
from .navigation_helper import NavigationHelper, NavigationInstruction

maskrcnn_model = None


class Session(APIView):
    """
    Creates a new skin tone detection session or updates it.
    """

    def get(self, request):
        qp = UserIdSerializer(data=request.query_params)
        qp.is_valid(raise_exception=True)
        user_id = qp.get_user_id()

        try:
            with transaction.atomic(savepoint=False):
                user = User.objects.get(pk=user_id)
                session = SessionModelsManager.create_session(SessionState.NEW, user)
                session.save()

            return Response(status=status.HTTP_201_CREATED, data=SessionResponseHelper.new_session_created_response(
                session.id))
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("User does not exist"))

    """
    Determines brightness of surroundings and updates session.
    """

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Session.load_maskrcnn_model()

        session_id = serializer.get_session_id()

        # For debugging purposes only. In production, we would upload the image to blob store like Amazon S3.
        serializer.save_image_to_file()

        # Detect lighting conditions.
        skin_tone_analyzer = SkinToneAnalyzer(maskrcnn_model, Session.get_skin_detection_config(serializer.get_image()))

        try:
            scene_brightness_and_direction = skin_tone_analyzer.get_primary_light_direction_and_scene_brightness()
            print("\nScene Brightness and Direction: ", scene_brightness_and_direction, "\n")
            navigation_instruction = NavigationHelper.get_instruction(scene_brightness_and_direction)
        except TeethNotVisibleException:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=create_response_message_with_error_code(
                "User teeth not visible", 101))

        skin_tones = []
        if navigation_instruction == NavigationInstruction.NEUTRAL_LIGHTING_STOP:
            # User is in neutral lighting. Compute skin tones.
            skin_tones = skin_tone_analyzer.get_skin_tones()

        try:
            with transaction.atomic(savepoint=False):
                session = SkinToneDetectionSession.objects.get(pk=session_id)
                session = SessionModelsManager.update_session_state(session, SessionState.IN_PROGRESS)
                session.save()

                session_image = SessionModelsManager.create_image(session, scene_brightness_and_direction,
                                                                  navigation_instruction)
                if navigation_instruction == NavigationInstruction.NEUTRAL_LIGHTING_STOP:
                    model_skin_tones = SessionModelsManager.create_skin_tones(skin_tones, session_image)
                    for model_skin_tone in model_skin_tones:
                        model_skin_tone.save()

                session_image.save()

            return Response(status=status.HTTP_200_OK, data=SessionResponseHelper.create_navigation_and_skin_tones_response(
                session.id, navigation_instruction, skin_tones))
        except SkinToneDetectionSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("Session does not exist"))

    """
    Completes the given session if not completed already.
    """

    def put(self, request):
        serializer = SessionIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.get_session_id()

        try:
            with transaction.atomic(savepoint=False):
                session = SkinToneDetectionSession.objects.get(pk=session_id)
                if not SessionModelsManager.is_state_complete(session):
                    session = SessionModelsManager.update_session_state(session, SessionState.COMPLETE)
                    session.save()

            return Response(status=status.HTTP_200_OK, data=SessionResponseHelper.session_ended_response(session_id))

        except SkinToneDetectionSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("Session does not exist"))

    """
    Loads MaskRCNN model once per process.
    """

    @staticmethod
    def load_maskrcnn_model():
        global maskrcnn_model
        if maskrcnn_model is None:
            maskrcnn_model = SkinToneAnalyzer.construct_model(
                "/Users/addarsh/virtualenvs/aws_train/src/maskrcnn_model/mask_rcnn_face_0060.h5")

    @staticmethod
    def get_skin_detection_config(image: np.ndarray):
        skin_detection_config = SkinDetectionConfig()
        skin_detection_config.IMAGE = image
        skin_detection_config.USE_NEW_CLUSTERING_ALGORITHM = True
        return skin_detection_config
