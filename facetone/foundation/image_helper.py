import numpy as np
import cv2
import base64
from facemagik.utils import ImageUtils
from facemagik.skintone import FaceMaskInfo, NoseMiddlePoint
from PIL import Image

"""
Helper class for image related operations.
"""


class ImageHelper:

    @staticmethod
    def get_image(base64_str):
        decoded_bytes = base64.b64decode(base64_str)
        im_arr = np.frombuffer(decoded_bytes, dtype=np.uint8)
        cv_image = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        return cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

    @staticmethod
    def create_face_mask_info_from_contour_points(image: np.ndarray, face_till_nose_end_cpts: np.ndarray,
                                                  left_eye_cpts: np.ndarray, right_eye_cpts: np.ndarray,
                                                  left_eyebrow_cpts: np.ndarray, right_eyebrow_cpts: np.ndarray,
                                                  mouth_without_lips_cpts: np.ndarray, nose_middle_point):
        # Create masks of contour points.
        image_shape = image.shape[:2]
        face_mask = ImageUtils.get_face_mask_till_nose_end(image_shape, face_till_nose_end_cpts, left_eye_cpts,
                                                           right_eye_cpts, left_eyebrow_cpts, right_eyebrow_cpts)
        mouth_without_lips_mask = ImageUtils.get_mask_from_contour_points(image_shape, mouth_without_lips_cpts)
        left_eye_mask = ImageUtils.get_mask_from_contour_points(image_shape, left_eye_cpts)
        right_eye_mask = ImageUtils.get_mask_from_contour_points(image_shape, right_eye_cpts)

        return FaceMaskInfo(face_mask_to_process=face_mask, mouth_mask_to_process=mouth_without_lips_mask,
                            nose_middle_point=NoseMiddlePoint(x=nose_middle_point[0], y=nose_middle_point[1]),
                            left_eye_mask=left_eye_mask, right_eye_mask=right_eye_mask)

    @staticmethod
    def save_image_to_file(image_name, img):
        im = Image.fromarray(img)
        with open("displayP3_icc_profile.txt", "rb") as f:
            icc = f.read()
        im.save(image_name, icc_profile=icc)
