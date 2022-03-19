from rest_framework import serializers
from PIL import Image
import base64
import binascii
import numpy as np


class UserIdSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

    def get_user_id(self) -> str:
        return self.validated_data["user_id"]


class SessionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    image_name = serializers.CharField(allow_blank=False, allow_null=False)
    image = serializers.CharField()
    image_shape = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=3, max_length=3)

    def validate_image_name(self, value) -> str:
        if not value.endswith(".png"):
            raise serializers.ValidationError("Invalid image name")
        return value

    def validate_image(self, value) -> str:
        try:
            base64.b64decode(value, validate=True)
        except binascii.Error:
            raise serializers.ValidationError("Invalid base64 encoding for image")
        return value

    def validate_image_shape(self, value) -> list:
        if value[2] != 3:
            raise serializers.ValidationError("Image does not have 3 channels")
        return value

    def get_session_id(self) -> str:
        return self.validated_data["session_id"]

    def get_image_name(self) -> str:
        return self.validated_data["image_name"]

    def get_image(self) -> np.ndarray:
        base64_str = self.validated_data["image"]
        decoded_bytes = base64.b64decode(base64_str)
        return np.reshape(np.frombuffer(decoded_bytes, dtype=np.uint8), self.get_image_shape())

    def get_image_shape(self) -> tuple:
        return tuple(self.validated_data["image_shape"])

    def save_image_to_file(self):
        im = Image.fromarray(self.get_image())
        with open("displayP3_icc_profile.txt", "rb") as f:
            icc = f.read()
        im.save(self.get_image_name(), icc_profile=icc)


class SessionIdSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()

    def get_session_id(self) -> str:
        return self.validated_data["session_id"]
