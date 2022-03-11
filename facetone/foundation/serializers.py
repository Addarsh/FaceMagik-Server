from rest_framework import serializers


class SessionQueryParamsSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

    def get_user_id(self):
        return self.validated_data["user_id"]