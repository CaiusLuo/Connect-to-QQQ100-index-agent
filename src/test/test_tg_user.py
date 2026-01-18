from src.db.tg_user.user_service import UserService


def test_insert_user():
    update = {
        "message": {
            "from": {
                "id": 123456,
                "username": "caius_dev",
                "first_name": "Caius",
                "last_name": "Lin",
                "language_code": "zh-hans"
            }
        }
    }

    user_data = update["message"]["from"]

    # 订阅用户
    UserService.subscribe_user(user_data)
    print(user_data)

    # 查询订阅用户
    subscribed = UserService.list_subscribed_users()
    print(subscribed)

if __name__ == "__main__":
    test_insert_user()
