from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from social_core.backends.yandex import YandexOAuth2

UserModel = get_user_model()

class AsyncModelBackend(ModelBackend):

    async def aget_user(self, user_id: int):
        try:
            user = await UserModel._default_manager.aget(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None


class YandexOAuth2Backend(YandexOAuth2):
    # Setting this to false allows to use frontend auth flow
    STATE_PARAMETER = True