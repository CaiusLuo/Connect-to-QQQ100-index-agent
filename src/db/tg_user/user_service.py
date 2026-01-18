from .tg_user import TgUser
from .tg_user_repo import TgUserRepo

class UserService:

    @staticmethod
    def subscribe_user(user_data: dict):
        user = TgUser(
            tg_user_id=user_data.get("id"),
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code"),
            is_subscribed=True
        )
        TgUserRepo.upsert(user)
    
    @staticmethod
    def unsubscribe_user(user_data: dict):
        user = TgUser(
            tg_user_id=user_data.get("id"),
            is_subscribed=False
        )
        TgUserRepo.upsert(user)

    @staticmethod
    def list_subscribed_users():
        return TgUserRepo.get_subscribed_users()