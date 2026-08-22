"""Fetch one daily picture and deliver it through WxPusher with no text."""

from __future__ import annotations

import logging
import os
import random
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests
from requests import Response
from requests.exceptions import RequestException

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message"
DEFAULT_POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"
CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 60

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ImageSourceError(RuntimeError):
    """An image provider could not return a usable public image URL."""


class PushError(RuntimeError):
    """WxPusher could not accept the image-only message."""


@dataclass(frozen=True)
class Settings:
    wxpusher_app_token: str
    wxpusher_uids: list[str]
    pexels_api_key: str | None
    pollinations_api_key: str | None
    pollinations_base_url: str
    fallback_image_urls: list[str]
    image_width: int
    image_height: int

    @classmethod
    def from_environment(cls) -> "Settings":
        app_token = require_environment("WXPUSHER_APP_TOKEN")
        uids = split_csv(require_environment("WXPUSHER_UIDS"))
        if not uids:
            raise ValueError("WXPUSHER_UIDS must contain at least one UID.")

        return cls(
            wxpusher_app_token=app_token,
            wxpusher_uids=uids,
            pexels_api_key=os.getenv("PEXELS_API_KEY"),
            pollinations_api_key=os.getenv("POLLINATIONS_API_KEY"),
            pollinations_base_url=os.getenv(
                "POLLINATIONS_BASE_URL", DEFAULT_POLLINATIONS_BASE_URL
            ).rstrip("/"),
            fallback_image_urls=split_csv(os.getenv("FALLBACK_IMAGE_URLS", "")),
            image_width=int(os.getenv("IMAGE_WIDTH", "1024")),
            image_height=int(os.getenv("IMAGE_HEIGHT", "1024")),
        )


def require_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable {name} is not configured.")
    return value


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def request_or_raise(
    method: str, url: str, *, timeout: tuple[int, int], **kwargs: Any
) -> Response:
    """Make one HTTP request and normalize network failures."""
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except RequestException as error:
        raise ImageSourceError(f"{method} request failed: {error}") from error


def random_pexels_query() -> str:
    return random.choice(
        [
            "busy street market", "friends having dinner", "traveler at train station",
            "child flying kite", "mountain hiking group", "dog in a park",
            "rainy city street", "family cooking together", "office team meeting",
            "sunset beach walk",
        ]
    )


def get_pexels_image(settings: Settings) -> str:
    if not settings.pexels_api_key:
        raise ImageSourceError("PEXELS_API_KEY is not configured.")

    try:
        response = request_or_raise(
            "GET", PEXELS_SEARCH_URL,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            headers={"Authorization": settings.pexels_api_key, "Accept": "application/json"},
            params={
                "query": random_pexels_query(),
                "orientation": random.choice(["landscape", "portrait", "square"]),
                "per_page": 30,
            },
        )
        photos = response.json().get("photos", [])
        if not photos:
            raise ImageSourceError("Pexels returned no photos.")
        source = random.choice(photos).get("src", {})
        image_url = source.get("large2x") or source.get("large") or source.get("original")
        if not isinstance(image_url, str) or not image_url.startswith("https://"):
            raise ImageSourceError("Pexels returned no usable HTTPS image URL.")
        return image_url
    except ImageSourceError:
        raise
    except (ValueError, TypeError, KeyError) as error:
        raise ImageSourceError(f"Invalid Pexels response: {error}") from error


def random_fantasy_prompt() -> str:
    subjects = ["a young explorer", "a curious fox", "two old friends", "a tiny dragon", "a violin player", "a brave astronaut"]
    places = ["inside a floating library", "on a moonlit bridge", "beside a hidden waterfall", "in a clockwork city", "above a misty forest", "at a lantern festival in the clouds"]
    details = ["with glowing paper birds", "while silver fish fly through the air", "under a sky full of constellations", "with a mysterious map in hand", "as warm light shines from distant windows", "surrounded by ancient blue flowers"]
    styles = ["cinematic fantasy illustration", "storybook artwork", "highly detailed digital painting", "dreamlike cinematic scene"]
    return f"{random.choice(subjects)} {random.choice(places)}, {random.choice(details)}, {random.choice(styles)}, clear central subject, safe for all audiences, no text"


def get_pollinations_image(settings: Settings) -> str:
    image_url = f"{settings.pollinations_base_url}/{quote(random_fantasy_prompt(), safe='')}"
    headers = ({"Authorization": f"Bearer {settings.pollinations_api_key}"}
               if settings.pollinations_api_key else {})
    try:
        response = request_or_raise(
            "GET", image_url,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            headers=headers,
            params={
                "width": settings.image_width, "height": settings.image_height,
                "seed": random.randint(1, 2_147_483_647), "model": "flux", "safe": "true",
            },
            stream=True,
        )
        content_type = response.headers.get("Content-Type", "").lower()
        prepared_url = response.url
        response.close()
        if not content_type.startswith("image/"):
            raise ImageSourceError(f"Pollinations returned non-image content: {content_type or 'missing'}")
        if not prepared_url.startswith("https://"):
            raise ImageSourceError("Pollinations returned a non-HTTPS image URL.")
        return prepared_url
    except ImageSourceError:
        raise
    except (ValueError, TypeError) as error:
        raise ImageSourceError(f"Invalid Pollinations response: {error}") from error


def get_fallback_image(settings: Settings) -> str:
    if not settings.fallback_image_urls:
        raise ImageSourceError("Both remote sources failed and FALLBACK_IMAGE_URLS is not configured.")
    image_url = random.choice(settings.fallback_image_urls)
    if not image_url.startswith("https://"):
        raise ImageSourceError("Fallback image URL must use HTTPS.")
    return image_url


def choose_image_url(settings: Settings) -> tuple[str, str]:
    primary, secondary = (("pexels", "pollinations") if random.random() < 0.5
                          else ("pollinations", "pexels"))
    providers = {"pexels": get_pexels_image, "pollinations": get_pollinations_image}
    for source in (primary, secondary):
        try:
            image_url = providers[source](settings)
            logger.info("Selected image source: %s", source)
            return image_url, source
        except ImageSourceError as error:
            logger.warning("%s source failed; trying next route: %s", source, error, exc_info=True)
    image_url = get_fallback_image(settings)
    logger.warning("Both remote sources failed; using configured fallback image.")
    return image_url, "fallback"


def send_image_only(settings: Settings, image_url: str) -> None:
    payload = {
        "appToken": settings.wxpusher_app_token,
        "content": f'<img src="{image_url}" />',
        "contentType": 2,
        "uids": settings.wxpusher_uids,
        "verifyPayType": 0,
    }
    try:
        response = requests.post(
            WXPUSHER_SEND_URL, json=payload,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
        body = response.json()
    except RequestException as error:
        raise PushError(f"WxPusher network request failed: {error}") from error
    except ValueError as error:
        raise PushError(f"WxPusher returned invalid JSON: {error}") from error
    if body.get("code") not in (None, 1000):
        raise PushError(f"WxPusher rejected the message: {body.get('msg', 'unknown error')}")


def main() -> None:
    settings = Settings.from_environment()
    image_url, source = choose_image_url(settings)
    send_image_only(settings, image_url)
    logger.info("Image-only push succeeded via %s.", source)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ImageSourceError, PushError) as error:
        logger.error("Daily image push failed: %s", error, exc_info=True)
        raise SystemExit(1) from error
