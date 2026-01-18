from dataclasses import dataclass

@dataclass
class TgUser:
    tg_user_id: int
    username: str = None
    first_name: str = None
    last_name: str = None
    language_code: str = None
    is_subscribed: str = None