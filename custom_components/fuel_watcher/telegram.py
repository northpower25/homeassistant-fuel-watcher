import async_timeout

async def send_telegram(hass, token, chat_id, text):
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    session = hass.helpers.aiohttp_client.async_get_clientsession()

    payload = {"chat_id": chat_id, "text": text}

    try:
        async with async_timeout.timeout(10):
            await session.post(url, json=payload)
    except Exception:
        pass
