from django.contrib.auth.backends import ModelBackend

class CustomUserBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return True

    def get_user(self, user_id):
        try:
            return self.get_queryset().get(pk=user_id)
        except self.model.DoesNotExist:
            return None