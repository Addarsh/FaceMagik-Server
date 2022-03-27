from rest_framework import serializers

class UserIdSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

    def get_user_id(self) -> str:
        return self.validated_data["user_id"]


class SessionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    image_name = serializers.CharField(allow_blank=False, allow_null=False)

    def validate_image_name(self, value) -> str:
        if not value.endswith(".png"):
            raise serializers.ValidationError("Invalid image name")
        return value

    def get_session_id(self) -> str:
        return self.validated_data["session_id"]

    def get_image_name(self) -> str:
        return self.validated_data["image_name"]


class SessionIdSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()

    def get_session_id(self) -> str:
        return self.validated_data["session_id"]
