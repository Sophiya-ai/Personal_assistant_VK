# код сервера для приема событий от ВКонтакте через механизм Callback API
#Callback API — это механизм, при котором VK отправляет HTTP-запросы на наш сервер,
# а сервер их принимает и реагирует.
# Без этих настроек мы не сможем получать сообщения от пользователя в сообществе.

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
#параметр, который нужен, чтобы вернуть простой текст (требование ВКонтакте)

app = FastAPI()

CONFIRMATION_TOKEN = "c15cbe1c"
#токен, который ВК требует для подтверждения того, что сервер принадлежит нам.
# Он указывается в коде как строка, которую должен вернуть сервер

#обработчик запроса. Когда приходит пост-запрос на vk/callback,
# то выполняется нижеописанная функция -
@app.post( "/vk/callback", response_class=PlainTextResponse)
async def vk_callback(request: Request) :
    data = await request. json() # получаем JSON-файл из запроса от ВК и выводим сообщение в консоль для отладки
    print("VK EVENT:", data) # просто выводим сообщение в консоль для отладки

    if data.get("type") == "confirmation":
        return CONFIRMATION_TOKEN
    # подтверждение сервера

    #ответ на остальные события, чтобы сервер не слал повторные запросы
    return "ok"