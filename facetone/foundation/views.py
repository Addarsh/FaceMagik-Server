import numpy as np
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import User, SkinToneDetectionSession
from .serializers import SessionSerializer, UserIdSerializer
from .response_helper import create_response_message
from .skin_tone_detection_session_helper import SkinToneDetectionSessionHelper, SkinToneSessionState
from facemagik.skintone import SkinToneAnalyzer, SkinDetectionConfig


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
        skin_tone_analyzer = Session.create_skin_analyzer(serializer.get_image())
        skin_tone_analyzer.get_scene_brightness_and_primary_light_direction()

        try:
            with transaction.atomic(savepoint=False):
                session = SkinToneDetectionSession.objects.get(pk=session_id)
        except SkinToneDetectionSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("Session does not exist"))

        return Response(status=status.HTTP_200_OK, data=SkinToneDetectionSessionHelper.create_response(
            session.id))

    """
    Creates a Skin Tone Analyzer object.
    """

    @staticmethod
    def create_skin_analyzer(image: np.ndarray):
        skin_detection_config = SkinDetectionConfig()
        skin_detection_config.IMAGE = image
        skin_detection_config.USE_NEW_CLUSTERING_ALGORITHM = True

        # Load MaskRCNN model. Currently using local path to the model.
        maskrcnn_model = SkinToneAnalyzer.construct_model(
            "/Users/addarsh/virtualenvs/aws_train/src/maskrcnn_model/mask_rcnn_face_0060.h5")

        return SkinToneAnalyzer(maskrcnn_model, skin_detection_config)
