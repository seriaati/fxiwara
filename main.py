from urllib.parse import unquote

import fastapi
import httpx
import uvicorn

app = fastapi.FastAPI()


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxiwara")


@app.get("/proxy")
async def video_proxy(
    url: str, path: str, expires: str, hash: str
) -> fastapi.responses.Response:
    url = unquote(url)
    proxy_url = f"{url}&path={path}&expires={expires}&hash={hash}"

    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        "referer": "https://iwara.tv/",
        "sec-ch-ua": '"Not;A=Brand";v="24", "Chromium";v="128"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "Android",
        "sec-fetch-dest": "video",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
    }
    async with httpx.AsyncClient() as client:
        video = await client.get(proxy_url, headers=headers)

    return fastapi.responses.Response(content=video.content, media_type="video/mp4")


@app.exception_handler(httpx.HTTPStatusError)
async def http_exception_handler(
    request: fastapi.Request, exc: httpx.HTTPStatusError
) -> fastapi.Response:
    return fastapi.Response(content=str(exc), status_code=exc.response.status_code)


@app.get("/video/{video_id}/{video_name}")
async def video_endpoint(
    video_id: str, video_name: str
) -> fastapi.responses.HTMLResponse:
    url = f"https://iwara.tv/video/{video_id}/{video_name}"
    api_url = f"https://api.iwara.tv/video/{video_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()

        file_url = data["fileUrl"]
        file_response = await client.get(
            file_url, headers={"x-version": "cc8b2b7d31592a95c1701fb0fb32b04d78e4de32"}
        )
        file_data = file_response.json()

        preview = next(d for d in file_data if d["name"] == "preview")
        video_url = "https:" + preview["src"]["download"]
        proxy_url = f"https://fxiwara.seria.moe/proxy?url={video_url}"

    html = f"""
    <html>
    
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#ed7042">
        <meta property="og:title" content="{data['user']['name']} - {data['title']}">
        <meta property="og:type" content="video">
        <meta property="og:site_name" content="👁️ Views: {data['numViews']}\n👍 Likes: {data['numLikes']}">
        <meta property="og:url" content="{url}">
        <meta property="og:video" content="{proxy_url}">
        <meta property="og:video:secure_url" content="{proxy_url}">
        <meta property="og:video:type" content="video/mp4">
        
        <script>
            window.onload = function() {{
                window.location.href = "{url}";
            }}
        </script>
    </head>
    
    <body>
        <p>Redirecting you to the Iwara video...</p>
        <p>If you are not redirected automatically, <a href="{url}">click here</a>.</p>
    </body>
    
    </html>
    """

    return fastapi.responses.HTMLResponse(content=html)


if __name__ == "__main__":
    uvicorn.run(app, port=7965)
