import os
import numpy as np
from enum import Enum
from . import models
from .image_helper import ImageHelper
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.utils import OperationalError
from facemagik.skintone import SkinToneAnalyzer, SkinDetectionConfig
from facemagik.common import LightDirection

maskrcnn_model = None


class UserSessionState(Enum):
    NEW = 1
    ROTATION_IN_PROGRESS = 2
    ROTATION_COMPLETE = 3


class UserSession(APIView):
    """
    Creates a user session associated with the given user.
    """

    def post(self, request):
        user_id = request.data["user_id"]

        try:
            with transaction.atomic(savepoint=False):
                user = models.User.objects.get(pk=user_id)
                user_session = models.UserSession(user=user, state=str(UserSessionState.NEW))
                user_session.save()

            return Response(status=status.HTTP_201_CREATED, data={"user_id": user_id, "user_session_id":
                user_session.id})
        except models.User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"user_id": user_id, "message": "User does not "
                                                                                                   "exist"})

    """
    Updates new state of user state.
    """

    def put(self, request):
        user_session_id = request.data["user_session_id"]
        new_state = request.data["new_state"]

        try:
            with transaction.atomic(savepoint=False):
                user_session = models.UserSession.objects.get(pk=user_session_id)
                user_session.state = new_state
                user_session.save()

            return Response(status=status.HTTP_200_OK, data={"user_session_id": user_session_id, "new_state":
                new_state, "message": "Updated new state"})
        except models.UserSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"user_session_id": user_session_id, "message":
                "User session does not exist"})


class RotationResult(APIView):
    """
    Returns result from Rotation mode computation. Throws an error if rotation mode is not complete or if the session
    doesn't exist.
    """

    def get(self, request):
        user_session_id = request.query_params.get("user_session_id")

        try:
            with transaction.atomic(savepoint=False):
                user_session = models.UserSession.objects.get(pk=user_session_id)
                if user_session.state != str(UserSessionState.ROTATION_IN_PROGRESS):
                    raise ValueError("User session state is not in rotation mode")

                # Fetch rotation images sorted by heading.
                rotation_images = models.RotationImage.objects.filter(user_session_id__exact=user_session_id).order_by(
                    "heading")
                primary_light_heading = RotationResult.compute_heading_of_primary_light_direction(rotation_images)

            print("Rotation result primary light heading: ", primary_light_heading)
            return Response(status=status.HTTP_200_OK, data={"user_session_id": user_session_id,
                                                             "primary_light_heading": primary_light_heading})
        except models.UserSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"user_session_id": user_session_id, "message":
                "User session does not exist"})
        except KeyError as ke:
            return Response(status=status.HTTP_412_PRECONDITION_FAILED, data={"user_session_id": user_session_id,
                                                                              "message": str(ke)})

    """
    Returns heading of primary light direction for given rotation images sorted by heading.
    """

    @staticmethod
    def compute_heading_of_primary_light_direction(rotation_images):
        # Find the sequence of consecutive CENTER directions with maximum average brightness.
        cur_max_brightness = -1
        cur_primary_heading = -1
        cur_heading_and_brightness_list = []
        for rotation_image in rotation_images:
            if rotation_image.primary_light_direction != str(LightDirection.CENTER):
                if len(cur_heading_and_brightness_list) > 0:
                    heading_list = [h[0] for h in cur_heading_and_brightness_list]
                    brightness_list = [h[1] for h in cur_heading_and_brightness_list]
                    mean_brightness = sum(brightness_list) / len(brightness_list)
                    mean_heading = sum(heading_list) / len(heading_list)
                    if mean_brightness > cur_max_brightness:
                        cur_max_brightness = mean_brightness
                        cur_primary_heading = mean_heading
                    cur_heading_and_brightness_list = []
                continue
            cur_heading_and_brightness_list.append(
                [rotation_image.heading, rotation_image.average_face_brightness_value])

        if cur_primary_heading == -1:
            raise KeyError("No primary light direction found in images")
        return round(cur_primary_heading)


class RotationImage(APIView):
    """
    Processes image uploaded as part of rotation mode.
    """

    def post(self, request):
        user_session_id = request.data["user_session_id"]
        heading = request.data["heading"]
        image = ImageHelper.get_image(request.data["image"])
        nose_middle_point = request.data["nose_middle_point"]
        face_till_nose_end_contour_points = request.data["face_till_nose_end_contour_points"]
        mouth_without_lips_contour_points = request.data["mouth_without_lips_contour_points"]
        left_eye_contour_points = request.data["left_eye_contour_points"]
        right_eye_contour_points = request.data["right_eye_contour_points"]
        left_eyebrow_contour_points = request.data["left_eyebrow_contour_points"]
        right_eyebrow_contour_points = request.data["right_eyebrow_contour_points"]

        # Process primary light direction.
        skin_tone_analyzer = SkinToneAnalyzer(maskrcnn_model=None,
                                              skin_config=RotationImage.get_skin_detection_config(image),
                                              face_mask_info=ImageHelper.create_face_mask_info_from_contour_points(
                                                  image=image, face_till_nose_end_cpts=np.array(
                                                      face_till_nose_end_contour_points),
                                                  left_eye_cpts=np.array(
                                                      left_eye_contour_points),
                                                  right_eye_cpts=np.array(
                                                      right_eye_contour_points),
                                                  left_eyebrow_cpts=np.array(
                                                      left_eyebrow_contour_points),
                                                  right_eyebrow_cpts=np.array(
                                                      right_eyebrow_contour_points),
                                                  mouth_without_lips_cpts=
                                                  np.array(mouth_without_lips_contour_points),
                                                  nose_middle_point=nose_middle_point))

        try:
            primary_light_direction = skin_tone_analyzer.get_light_direction()
        except Exception as e:
            print("Got PRIMARY LIGHT DIRECTION exception: ", e)
            raise e
        average_face_brightness_value = skin_tone_analyzer.get_average_face_brightness()

        if 'RDS_DB_NAME' not in os.environ:
            # For debugging purposes only. In production, we would upload the image to blob store like Amazon S3.
            ImageHelper.save_image_to_file("rotation_mode/" + str(heading) + "_" + str(primary_light_direction) + "_"
                                           + str(average_face_brightness_value) + ".png", image)

        max_num_transaction_attempts = 5
        transaction_attempts = 0
        while True:
            try:
                with transaction.atomic(savepoint=False):
                    user_session = models.UserSession.objects.get(pk=user_session_id)
                    user_session.state = str(UserSessionState.ROTATION_IN_PROGRESS)
                    user_session.save()

                    rotation_image = models.RotationImage(user_session=user_session, heading=heading,
                                                          primary_light_direction=str(primary_light_direction),
                                                          average_face_brightness_value=average_face_brightness_value)
                    rotation_image.save()

                print("Committed transaction on attempt number: ", transaction_attempts + 1)
                return Response(status=status.HTTP_201_CREATED, data={"user_session_id": user_session.id})
            except models.UserSession.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={"user_session_id": user_session_id, "message":
                    "User Session does not exist"})
            except OperationalError as oe:
                transaction_attempts += 1
                if transaction_attempts < max_num_transaction_attempts:
                    continue
                print("Exceeded max transaction attempts, failed with error: ", oe)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"user_session_id":
                                                                                        user_session_id, "message":
                                                                                        "Internal Server error, "
                                                                                        "failed to upload image"})

    @staticmethod
    def get_skin_detection_config(image):
        skin_detection_config = SkinDetectionConfig()
        skin_detection_config.IMAGE = image
        skin_detection_config.USE_NEW_CLUSTERING_ALGORITHM = True
        return skin_detection_config

    """
    Loads MaskRCNN model once per process.
    """

    @staticmethod
    def load_maskrcnn_model():
        global maskrcnn_model
        if 'RDS_DB_NAME' in os.environ:
            path_prefix = "/tmp/"
        else:
            path_prefix = "/Users/addarsh/virtualenvs/aws_train/src/maskrcnn_model/"
        if maskrcnn_model is None:
            maskrcnn_model = SkinToneAnalyzer.construct_model(
                path_prefix + "mask_rcnn_face_0060.h5")
