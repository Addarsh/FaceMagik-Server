import numpy as np
import base64
import cv2

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import User, SkinToneDetectionSession
from .serializers import SessionSerializer, UserIdSerializer, SessionIdSerializer
from .response_helper import create_response_message, create_response_message_with_error_code
from .session_models_manager import SessionModelsManager, SessionState, SessionResponseHelper
from facemagik.skintone import SkinToneAnalyzer, SkinDetectionConfig, TeethNotVisibleException, FaceMaskInfo, \
    NoseMiddlePoint
from facemagik.utils import ImageUtils
from .navigation_helper import NavigationHelper, NavigationInstruction
from PIL import Image

maskrcnn_model = None


class Session(APIView):
    """
    Creates a new skin tone detection session or updates it.
    """

    def get(self, request):
        qp = UserIdSerializer(data=request.query_params)
        qp.is_valid(raise_exception=True)
        user_id = qp.get_user_id()
        Session.load_maskrcnn_model()

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
        image_name = serializer.get_image_name()
        image = Session.get_image(request.data["image"])
        face_mask = Session.get_image(request.data["face_mask"])
        mouth_mask = Session.get_image(request.data["mouth_mask"])
        left_eye_mask = Session.get_image(request.data["left_eye_mask"])
        right_eye_mask = Session.get_image(request.data["right_eye_mask"])
        nose_middle_point = request.data["nose_middle_point"]
        face_till_nose_end_contour_points = request.data["face_till_nose_end_contour_points"]
        mouth_without_lips_contour_points = request.data["mouth_without_lips_contour_points"]
        mouth_with_lips_contour_points = request.data["mouth_with_lips_contour_points"]
        left_eye_contour_points = request.data["left_eye_contour_points"]
        right_eye_contour_points = request.data["right_eye_contour_points"]
        left_eyebrow_contour_points = request.data["left_eyebrow_contour_points"]
        right_eyebrow_contour_points = request.data["right_eyebrow_contour_points"]

        # For debugging purposes only. In production, we would upload the image to blob store like Amazon S3.
        Session.save_image_to_file(image_name, image)
        Session.save_image_to_file("test_face_mask.png", face_mask)
        Session.save_image_to_file("test_mouth_mask.png", mouth_mask)
        Session.save_image_to_file("left_eye_mask.png", left_eye_mask)
        Session.save_image_to_file("right_eye_mask.png", right_eye_mask)
        Session.save_nose_middle_point_to_file(nose_middle_point)
        Session.save_contour_points_to_file("face_till_nose_end_contour_points.txt", face_till_nose_end_contour_points)
        Session.save_contour_points_to_file("mouth_without_lips_contour_points.txt", mouth_without_lips_contour_points)
        Session.save_contour_points_to_file("mouth_with_lips_contour_points.txt", mouth_with_lips_contour_points)
        Session.save_contour_points_to_file("left_eye_contour_points.txt", left_eye_contour_points)
        Session.save_contour_points_to_file("right_eye_contour_points.txt", right_eye_contour_points)
        Session.save_contour_points_to_file("left_eyebrow_contour_points.txt", left_eyebrow_contour_points)
        Session.save_contour_points_to_file("right_eyebrow_contour_points.txt", right_eyebrow_contour_points)

        # Detect lighting conditions.
        face_mask_info = Session.create_face_mask_info(face_mask, mouth_mask, left_eye_mask, right_eye_mask,
                                                       nose_middle_point)
        skin_tone_analyzer = SkinToneAnalyzer(maskrcnn_model, Session.get_skin_detection_config(image), face_mask_info)

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

            return Response(status=status.HTTP_200_OK,
                            data=SessionResponseHelper.create_navigation_and_skin_tones_response(
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

    @staticmethod
    def create_face_mask_info(face_mask_to_process_rgb, mouth_mask_to_process_rgb, left_eye_mask_rgb,
                              right_eye_mask_rgb, nose_middle_point):
        face_mask_info = FaceMaskInfo(
            face_mask_to_process=Session.get_boolean_mask_from_rgb_image(face_mask_to_process_rgb),
            mouth_mask_to_process=Session.get_boolean_mask_from_rgb_image(mouth_mask_to_process_rgb),
            nose_middle_point=NoseMiddlePoint(x=nose_middle_point[0], y=nose_middle_point[1]),
            left_eye_mask=Session.get_boolean_mask_from_rgb_image(left_eye_mask_rgb),
            right_eye_mask=Session.get_boolean_mask_from_rgb_image(right_eye_mask_rgb))
        return face_mask_info

    @staticmethod
    def get_boolean_mask_from_rgb_image(rgb_image):
        return ImageUtils.get_boolean_mask(cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY))

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

    @staticmethod
    def get_image(base64_str):
        decoded_bytes = base64.b64decode(base64_str)
        im_arr = np.frombuffer(decoded_bytes, dtype=np.uint8)
        cv_image = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        return cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

    @staticmethod
    def save_image_to_file(image_name, img):
        im = Image.fromarray(img)
        with open("displayP3_icc_profile.txt", "rb") as f:
            icc = f.read()
        im.save(image_name, icc_profile=icc)

    @staticmethod
    def save_nose_middle_point_to_file(nose_middle_point):
        with open("nose_middle_point.txt", "w") as f:
            for v in nose_middle_point:
                f.write("%s\n" % v)

    @staticmethod
    def save_contour_points_to_file(fname, mouth_contour_points):
        with open(fname, "w") as f:
            f.write(str(mouth_contour_points))
