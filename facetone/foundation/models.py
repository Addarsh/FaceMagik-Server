import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

"""
Represents a user who logs in to the app.
"""


class User(AbstractUser):
    # Primary key uniquely identifying the user.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Email Address of the user.
    email = models.EmailField(_('email address'), unique=True)

    # Timestamp when this user row was last updated.
    last_updated = models.DateTimeField(auto_now=True)


"""
Skin Tone Detection session for a given user.
"""


class SkinToneDetectionSession(models.Model):
    # Primary key uniquely identifying the session.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Each session is associated with a AppUser.
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

    # Brightness value of scene in the image. Defaults to null.
    scene_brightness_value = models.IntegerField(null=True)

    # Scene Brightness description. Derived from scene brightness value.
    scene_brightness_description = models.CharField(max_length=200, blank=True)

    # Primary Light Direction in the image. Defaults to null.
    primary_light_direction = models.CharField(max_length=200, blank=True)

    # Navigation instruction given to user.
    navigation_instruction = models.CharField(max_length=200, blank=True)


"""
Skin tone from a neutral image uploaded by the user.
"""


class SkinTone(models.Model):
    # Primary key uniquely identifying the instance of the skin tone.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Image associated with given skin color.
    skin_tone_detection_image = models.ForeignKey(SkinToneDetectionImage, on_delete=models.CASCADE)

    # Timestamp when this skin tone row was added.
    create_timestamp = models.DateTimeField(auto_now_add=True)
    
    # RGB values of the skin tone. It's an array stored as a JSON string.
    rgb_values = models.CharField(max_length=200, blank=True)

    # Color profile. Usually display3 or sRGB.
    color_profile = models.CharField(max_length=200, blank=True)

    # Percentage of face mask covered by this color. Values are between 0 and 100.
    percentage_of_face_mask = models.IntegerField()

