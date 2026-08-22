"""Send one daily picture through WxPusher."""

from __future__ import annotations

import logging
import os
import random
import string
from urllib.parse import quote

import requests
from requests.exceptions import RequestException

WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message"
PICSUM_URL = "https://picsum.photos/seed/{seed}/{width}/{height}"
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"
TIMEOUT = (10, 60)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ImageError(RuntimeError):
    """Raised when an image provider cannot return a usable image."""


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def image_size() -> tuple[int, int]:
    return int(os.getenv("IMAGE_WIDTH", "1024")), int(os.getenv("IMAGE_HEIGHT", "1024"))


def validate_image(url: str, headers: dict[str, str] | None = None) -> str:
    """Fetch a public image URL once and return the final redirected URL."""
    try:
        response = requests.get(url, headers=headers or {}, timeout=TIMEOUT, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        final_url = response.url
        response.close()
    except RequestException as error:
        raise ImageError(f"Image request failed: {error}") from error

    if not content_type.startswith("image/") or not final_url.startswith("https://"):
        raise ImageError("Provider did not return a public image response.")
    return final_url


def get_picsum_image() -> str:
    width, height = image_size()
    seed = "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return validate_image(PICSUM_URL.format(seed=seed, width=width, height=height))


def fantasy_prompt() -> str:
    subjects = ["a young explorer", "a curious fox", "two old friends", "a tiny dragon"]
    places = ["inside a floating library", "on a moonlit bridge", "above a misty forest", "in a clockwork city"]
    details = ["with glowing paper birds", "under a sky full of constellations", "holding a mysterious map", "surrounded by ancient blue flowers"]
    styles = ["storybook illustration", "cinematic fantasy artwork", "dreamlike digital painting"]
    return (
        f"{random.choice(subjects)} {random.choice(places)}, "
        f"{random.choice(details)}, {random.choice(styles)}, "
        "safe for all audiences, clear central subject, no text"
    )


def get_pollinations_image() -> str:
    width, height = image_size()
    prompt = quote(fantasy_prompt(), safe="")
    url = f"{os.getenv('POLLINATIONS_BASE_URL', POLLINATIONS_BASE_URL).rstrip('/')}/{prompt}"
    params = {
        "width": width,
        "height": height,
        "seed": random.randint(1, 2_147_483_647),
        "model": "flux",
        "safe": "true",
    }
    api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    prepared = requests.Request("GET", url, params=params).prepare().url
    return validate_image(prepared, headers)


def choose_image() -> tuple[str, str]:
    primary, secondary = (("picsum", get_picsum_image), ("pollinations", get_pollinations_image))
    if random.random() >= 0.5:
        primary, secondary = secondary, primary

    for source, provider in (primary, secondary):
        try:
            image_url = provider()
            logger.info("Selected image source: %s", source)
            return image_url, source
        except (ImageError, ValueError) as error:
            logger.warning("%s failed; trying the other source: %s", source, error, exc_info=True)
    raise ImageError("Both image providers failed.")


def send_image(image_url: str) -> None:
    uids = [uid.strip() for uid in required("WXPUSHER_UIDS").split(",") if uid.strip()]
    if not uids:
        raise ValueError("WXPUSHER_UIDS contains no UID.")
    payload = {
        "appToken": required("WXPUSHER_APP_TOKEN"),
        "content": f'<img src="{image_url}" />',
        "contentType": 2,
        "uids": uids,
        "verifyPayType": 0,
    }
    try:
        response = requests.post(WXPUSHER_SEND_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        result = response.json()
    except (RequestException, ValueError) as error:
        raise RuntimeError(f"WxPusher request failed: {error}") from error
    if result.get("code") != 1000:
        raise RuntimeError(f"WxPusher rejected the message: {result.get('msg', 'unknown error')}")


def main() -> None:
    image_url, source = choose_image()
    send_image(image_url)
    logger.info("Daily image pushed successfully via %s.", source)


if __name__ == "__main__":
    try:
        main()
    except (ImageError, RuntimeError, ValueError) as error:
        logger.error("Daily push failed: %s", error, exc_info=True)
        raise SystemExit(1) from error
