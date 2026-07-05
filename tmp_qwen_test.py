import asyncio
import aiohttp
from backend.config import settings

config = settings.get_provider_config('custom_qwen')
endpoint = config.get('endpoint_url', '').strip()
username = config.get('username', '')
password = config.get('password', '')
print('endpoint=', endpoint)
print('username=', username)

async def main():
    auth = aiohttp.BasicAuth(username, password) if username or password else None
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.post(endpoint.rstrip('/') + '/api/chat', json={
            'model': 'qwen2.5:7b',
            'messages': [{'role': 'user', 'content': 'Say hello'}],
            'stream': False,
        }, timeout=aiohttp.ClientTimeout(total=45)) as resp:
            body = await resp.text()
            print('status=', resp.status)
            print(body[:2000])

asyncio.run(main())
