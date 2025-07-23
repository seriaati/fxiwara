from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
import uvicorn

import fastapi
from aiohttp_client_cache.session import CachedSession
from aiohttp_client_cache.backends.sqlite import SQLiteBackend


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    app.state.client = CachedSession(
        cache=SQLiteBackend(cache_name="cache.db", expire_after=3600),
    )
    try:
        yield
    finally:
        await app.state.client.close()


logger = logging.getLogger("uvicorn")
app = fastapi.FastAPI(lifespan=app_lifespan)


async def video_streamer(video_url: str) -> AsyncGenerator[bytes, None]:
    async with app.state.client.get(video_url) as resp:
        if resp.status != 200:
            raise fastapi.HTTPException(
                status_code=resp.status, detail="Error streaming video"
            )
        # Stream the content in chunks (here, 1MB per chunk)
        async for chunk in resp.content.iter_chunked(1024 * 1024):
            yield chunk


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxiwara")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/dl/{video_id}/{quality}")
async def download_video_endpoint(
    video_id: str, quality: str
) -> fastapi.responses.StreamingResponse:
    client: CachedSession = app.state.client
    api_url = f"https://api.iwara.tv/video/{video_id}"

    async with client.get(api_url) as resp:
        data = await resp.json()

    async with client.get(
        data["fileUrl"],
        headers={"x-version": "00d377d9a3d18587749666e69858d607e396fb5a"},
    ) as resp:
        file_response = await resp.json()

    video_data = next((d for d in file_response if d["name"] == quality), None)
    if video_data is None:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Quality {quality} not found."
        )

    video_url = f"https:{video_data['src']['download']}"

    return fastapi.responses.StreamingResponse(
        video_streamer(video_url), media_type="video/mp4"
    )


@app.get("/video/{video_id}/{video_name}")
async def video_endpoint(
    request: fastapi.Request, video_id: str, video_name: str
) -> fastapi.responses.Response:
    client: CachedSession = app.state.client
    url = f"https://iwara.tv/video/{video_id}/{video_name}"

    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    api_url = f"https://api.iwara.tv/video/{video_id}"

    try:
        async with client.get(api_url) as resp:
            data = await resp.json()
    except Exception:
        logger.exception("Failed to fetch video data.")
        return fastapi.responses.RedirectResponse(url)

    html = f"""
    <html>
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#ed7042">
        <meta property="og:title" content="{data["user"]["name"]} - {data["title"]}">
        <meta property="og:description" content="{data["body"]}">
        <meta property="og:site_name" content="👁️ Views: {data["numViews"]}\n👍 Likes: {data["numLikes"]}">
        <meta property="og:url" content="{url}">
    </head>
    </html>
    """

    return fastapi.responses.HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, port=7965)
