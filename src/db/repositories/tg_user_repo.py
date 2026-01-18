from src.db.models.tg_user import TgUser
from src.db.config import get_conn

class TgUserRepo:

    @staticmethod
    def upsert(user: TgUser):
        sql = """
        INSERT INTO tg_user (
            tg_user_id, username, first_name, last_name, language_code, is_subscribed
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (tg_user_id)
        DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            language_code = EXCLUDED.language_code,
            is_subscribed = EXCLUDED.is_subscribed,
            updated_at = now();
        """
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (
                user.tg_user_id,
                user.username,
                user.first_name,
                user.last_name,
                user.language_code,
                user.is_subscribed
            ))
            conn.commit()
    
    @staticmethod
    def get_subscribed_users():
        sql = "SELECT tg_user_id, username, first_name, last_name FROM tg_user WHERE is_subscribed = TRUE;"
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()