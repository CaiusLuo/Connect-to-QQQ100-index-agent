import requests
import json
import sys


def test_stream():
    url = "http://localhost:8000/invoke"
    print(f"📡 Connecting to {url}...")

    try:
        # stream=True 是关键
        with requests.post(url, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return

            print("✅ Connected! Waiting for events...\n")

            # 迭代读取流式响应
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data: "):
                        # 提取 JSON 数据
                        json_str = decoded_line[6:]
                        try:
                            data = json.loads(json_str)

                            if data["type"] == "log":
                                # 打印日志，不换行或者是动态刷新
                                print(f"{data['content']}")
                            elif data["type"] == "result":
                                print("\n" + "=" * 50)
                                print("🎉 FINAL RESULT:")
                                print("=" * 50)
                                print(data["content"])
                            elif data["type"] == "error":
                                print(f"\n❌ ERROR: {data['content']}")

                        except json.JSONDecodeError:
                            print(f"Raw data: {decoded_line}")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nConnection failed: {e}")


if __name__ == "__main__":
    test_stream()
