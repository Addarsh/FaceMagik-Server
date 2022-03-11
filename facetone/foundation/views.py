from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from .models import User
from .serializers import SessionQueryParamsSerializer
from .response_helper import create_response_message
from .skin_tone_detection_session_helper import SkinToneDetectionSessionHelper, SkinToneSessionState


@api_view(["GET", "POST"])
def session_handler(request):
    """
    Creates a new skin tone detection session or updates it.
    """
    if request.method == "GET":
        qp = SessionQueryParamsSerializer(data=request.query_params)
        qp.is_valid(raise_exception=True)
        user_id = qp.get_user_id()

        try:
            with transaction.atomic(savepoint=False):
                user = User.objects.get(pk=user_id)
                session = SkinToneDetectionSessionHelper.create(SkinToneSessionState.NEW, user)
                session.save()
                return Response(status=status.HTTP_201_CREATED, data=SkinToneDetectionSessionHelper.create_response(
                    session.id))
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data=create_response_message("User does not exist"))

    return Response(status=status.HTTP_403_FORBIDDEN)
