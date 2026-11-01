# ThemeGram Auto Attheme Generator API

A small FastAPI service that turns an uploaded image into a Telegram Android `.attheme` file using local Pillow color analysis. It is designed for one trusted ThemeGram bot server, protected by one shared API key.

> Status: implementation submitted for review in the linked pull request. Run the test suite in your deployment environment before exposing the API publicly.

## Features

- Local dominant-color extraction with Pillow; no AI API or paid external service.
- Curated Telegram Android theme template and explicit key-to-color mapping.
- Replaces only mapped theme keys; leaves all other template entries unchanged.
- One API key, file validation, upload limits, in-memory rate limiting, and no persistent image storage.
- FastAPI endpoint: `POST /api/v1/generate`; public `GET /health`.

## Requirements

- Python 3.11+
- pip

## Install and run (Termux or Linux)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Generate a strong API key and put it in `.env` as `API_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then run:

```bash
python run.py
```

The local API is available at `http://127.0.0.1:8000`. Interactive docs are at `/docs` in development. Do not expose the development server directly to the public internet.

## API

### `POST /api/v1/generate`

Headers:

```text
X-API-Key: YOUR_SECRET_API_KEY
```

Multipart form field: `image` (JPEG, PNG, or WEBP; maximum 10 MiB).

Returns `generated_theme.attheme` as `application/octet-stream`.

Example with cURL:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "X-API-Key: YOUR_SECRET_API_KEY" \
  -F "image=@wallpaper.jpg" \
  --output generated_theme.attheme
```

Example with Python `requests`:

```python
import requests

with open("wallpaper.jpg", "rb") as image:
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/generate",
        headers={"X-API-Key": "YOUR_SECRET_API_KEY"},
        files={"image": ("wallpaper.jpg", image, "image/jpeg")},
        timeout=30,
    )
response.raise_for_status()
with open("generated_theme.attheme", "wb") as output:
    output.write(response.content)
```

### Health check

```bash
curl http://127.0.0.1:8000/health
```

`/health` intentionally reveals no secrets or internal configuration.

## Aiogram 3.x integration

Keep `THEME_API_URL` and `THEME_API_KEY` in the bot server's environment. Never send the API key to Telegram users or put it in public source code.

```python
import os
import aiohttp
from aiogram.types import BufferedInputFile

THEME_API_URL = os.environ["THEME_API_URL"].rstrip("/")
THEME_API_KEY = os.environ["THEME_API_KEY"]

async def create_attheme(image_bytes: bytes) -> bytes:
    timeout = aiohttp.ClientTimeout(total=30)
    form = aiohttp.FormData()
    form.add_field("image", image_bytes, filename="wallpaper.jpg",
                   content_type="application/octet-stream")
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{THEME_API_URL}/api/v1/generate",
            data=form,
            headers={"X-API-Key": THEME_API_KEY},
        ) as response:
            if response.status != 200:
                # Avoid forwarding internal server details to the end user.
                raise RuntimeError(f"Theme API failed with HTTP {response.status}")
            return await response.read()

# Inside an aiogram message handler after receiving a photo:
# photo = message.photo[-1]
# buffer = await bot.download(photo)
# attheme_bytes = await create_attheme(buffer.getvalue())
# await message.answer_document(
#     BufferedInputFile(attheme_bytes, filename="ThemeGram.attheme"),
#     caption="Your theme is ready!",
# )
```

## Tests

```bash
pytest -q
```

## Production deployment

1. Run behind a trusted HTTPS reverse proxy (for example, Caddy or Nginx with TLS).
2. Set a strong `API_KEY` as a server environment secret; do not commit `.env`.
3. Restrict inbound traffic to HTTPS and, if practical, allowlist the bot server's outbound IP at the proxy/firewall.
4. Keep request body limits at the proxy (at least the configured 10 MiB file cap plus multipart overhead).
5. Use one Uvicorn worker if relying on the built-in in-memory rate limiter. For multiple workers, enforce rate limits at the reverse proxy instead.
6. Disable debug mode and do not expose `/docs` publicly unless protected at the proxy.
7. Rotate the API key immediately if it is exposed.

## Security notes

- The API key authenticates the trusted bot server, not an individual Telegram user. The bot must perform its own user-facing authorization and abuse controls.
- Images are processed in memory and are not intentionally persisted.
- The application checks actual decoded image format, dimensions, pixel count, and file size. The reverse proxy must also enforce a request-body limit because multipart parsing occurs before route code receives the upload.
- Rate limiting is process-local; use a single worker or enforce it at the proxy.
- Use HTTPS in production. Do not put secrets in query parameters, logs, screenshots, or bot replies.

## Theme compatibility

The template contains a deliberately selected set of Telegram Android theme keys sourced from Telegram-FOSS's bundled `night.attheme` asset. Only keys listed in `config/color_mapping.json` are changed. The upstream asset is version-dependent; test the generated theme in the exact Telegram Android client version you support. This project does not claim compatibility with Telegram iOS or every third-party fork.

## License and attribution

No separate license has been declared for this project yet. The small sample theme-key template is adapted from the Telegram-FOSS `night.attheme` asset; consult the upstream repository's license and retain its attribution/license terms when redistributing that asset.