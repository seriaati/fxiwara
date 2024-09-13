import fastapi
import httpx
import uvicorn

app = fastapi.FastAPI()


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxiwara")


@app.get("/dl/{video_id}/{quality}")
async def download_video_endpoint(
    video_id: str, quality: str
) -> fastapi.responses.RedirectResponse:
    api_url = f"https://api.iwara.tv/video/{video_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()
        file_url = data["fileUrl"]

        file_data = await client.get(
            file_url, headers={"x-version": "00d377d9a3d18587749666e69858d607e396fb5a"}
        )
        file_response = file_data.json()
        video_data = next((d for d in file_response if d["name"] == quality), None)

        if video_data is None:
            raise fastapi.HTTPException(
                status_code=404, detail=f"Quality {quality} not found."
            )

        return fastapi.responses.RedirectResponse(video_data["src"]["download"])


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
