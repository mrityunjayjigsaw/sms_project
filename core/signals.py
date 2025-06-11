from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, School

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # You can assign a default school if needed, or leave it blank
        school = School.objects.first()
        if school:
            UserProfile.objects.create(user=instance, school=School.objects.first())
