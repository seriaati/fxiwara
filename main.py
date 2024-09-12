import fastapi
import httpx
import uvicorn

app = fastapi.FastAPI()


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxiwara")


@app.get("/video/{video_id}/{video_name}")
async def video_endpoint(
    video_id: str, video_name: str
) -> fastapi.responses.HTMLResponse:
    url = f"https://iwara.tv/video/{video_id}/{video_name}"
    api_url = f"https://api.iwara.tv/video/{video_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()

    html = f"""
    <html>
    
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#ed7042">
        <meta property="og:title" content="{data['user']['name']} - {data['title']}">
        <meta property="og:description" content="{data['body']}">
        <meta property="og:site_name" content="👁️ Views: {data['numViews']}\n👍 Likes: {data['numLikes']}">
        <meta property="og:url" content="{url}">
        
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
