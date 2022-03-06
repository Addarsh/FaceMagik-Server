import uuid
from django.db import models

"""
Represents a user who logs in to the app.
"""


class User(models.Model):
    # Primary key uniquely identifying a user.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Timestamp when this user row was first created.
    create_timestamp = models.DateTimeField(auto_now_add=True)

    # First Name of the user.
    first_name = models.CharField(max_length=200, blank=True)

    # Last Name of the user.
    last_name = models.CharField(max_length=200, blank=True)

    # Email Address of the user.
    email = models.CharField(max_length=200, blank=True)

    # Timestamp when this user row was last updated.
    update_timestamp = models.DateTimeField(auto_now=True)


"""
Skin Tone Detection session for a given user.
"""


class SkinToneDetectionSession(models.Model):
    # Primary key uniquely identifying the session.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Each session is associated with a User.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Timestamp when this session row was first created.
    create_timestamp = models.DateTimeField(auto_now_add=True)

    # Timestamp when this session row was last updated.
    update_timestamp = models.DateTimeField(auto_now=True)

    # State of session.
    state = models.CharField(max_length=200, blank=True)


"""
Image uploaded in a skin tone detection session.
"""


class SkinToneDetectionImage(models.Model):
    # Primary key uniquely identifying the image.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Each image is associated with a skin tone detection session.
    skin_tone_detection_session = models.ForeignKey(SkinToneDetectionSession, on_delete=models.CASCADE)

    # Timestamp when this image row was created.
    create_timestamp = models.DateTimeField(auto_now_add=True)

    # Relative path of stored image. The full path can be on cloud (e.g. Amazon S3) or local development instance (
    # macOS filesystem).
    relative_image_path = models.CharField(max_length=200, blank=True)






