import numpy as np

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import User, SkinToneDetectionSession
from .serializers import SessionSerializer, UserIdSerializer
from .response_helper import create_response_message, create_response_message_with_error_code
from .skin_tone_detection_session_helper import SkinToneDetectionSessionHelper, SkinToneSessionState
from facemagik.skintone import SkinToneAnalyzer, SkinDetectionConfig, TeethNotVisibleException
from .navigation_helper import NavigationHelper


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
                session = SkinToneDetectionSessionHelper.create(SkinToneSessionState.NEW, user)
                return Response(status=status.HTTP_201_CREATED, data=SkinToneDetectionSessionHelper.create_response(
                    session.id))
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("User does not exist"))

    """
    Determines brightness of surroundings and updates session.
    """

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.get_session_id()

        # For debugging purposes only. In production, we would upload the image to blob store like Amazon S3.
        serializer.save_image_to_file()

        # Detect lighting conditions.
        global maskrcnn_model
        if maskrcnn_model is None:
            Session.load_maskrcnn_model()
        skin_tone_analyzer = SkinToneAnalyzer(maskrcnn_model, Session.get_skin_detection_config(serializer.get_image()))

        try:
            scene_brightness_and_direction = skin_tone_analyzer.get_scene_brightness_and_primary_light_direction()
            print("\nScene Brightness and Direction: ", scene_brightness_and_direction, "\n")
            navigation_instruction = NavigationHelper.get_instruction(scene_brightness_and_direction)
        except TeethNotVisibleException:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=create_response_message_with_error_code(
                "User teeth not visible", 101))

        try:
            with transaction.atomic(savepoint=False):
                session = SkinToneDetectionSession.objects.get(pk=session_id)
        except SkinToneDetectionSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("Session does not exist"))

        return Response(status=status.HTTP_200_OK, data=SkinToneDetectionSessionHelper.create_navigation_response(
            session.id, navigation_instruction))


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
