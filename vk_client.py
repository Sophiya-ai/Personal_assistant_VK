# модуль, который отправляет сообщения в ВКонтакте
# отдельно, т к - это правило хорошего тона при создании архитектуры ассистентов.
# Весь смысл этого файла можно обернуть в простую функцию send_vk_message(Отправить сообщение ВКонтакте).
# Хотя эту часть кода можно было добавить в файл app.py, вынесение ее в отдельный модуль делает код чище:
# каждый блок отвечает за свою зону ответственности.
import random
import requests
from config import VK_GROUP_TOKEN, VK_API_VERSION

VK_API_URL = "https://api.vk.com/method/messages.send"


def send_vk_message(peer_id: int, text: str) -> None:
    payload = {
        "access_token": VK_GROUP_TOKEN,
        "v": VK_API_VERSION,
        "peer_id": peer_id,
        "random_id": random.randint(1, 2_147_483_647),
        "message": text,
    }

    response = requests.post(VK_API_URL, data=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"VK API error: {data['error']}")