from fastapi import FastAPI, HTTPException
import os
import requests

from moviebox_api.v3.http_client import MovieBoxHttpClient
from moviebox_api.v3.core import DownloadableFilesDetail
from moviebox_api.v3.download import resolve_media_file_to_be_downloaded
from moviebox_api.v3.constants import CustomResolutionType

app = FastAPI()

# -----------------------
# TMDB CONFIG
# -----------------------
TMDB_API_KEY = "e1d304dda8b47424245c3c62fe9baea2"
TMDB_URL = "https://api.themoviedb.org/3/search/movie"


# -----------------------
# HEALTH CHECK
# -----------------------
@app.get("/")
def home():
    return {"status": "MovieBox + TMDB API running"}


# -----------------------
# TMDB SEARCH (NEW)
# -----------------------
@app.get("/search")
def search_movie(query: str = None):
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    try:
        res = requests.get(TMDB_URL, params={
            "api_key": TMDB_API_KEY,
            "query": query
        })

        data = res.json()

        results = []

        for m in data.get("results", [])[:10]:
            results.append({
                "title": m.get("title"),
                "id": m.get("id"),
                "release_date": m.get("release_date")
            })

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# MOVIEBOX LINKS
# -----------------------
async def get_links(subject_id):
    async with MovieBoxHttpClient() as client:
        details = DownloadableFilesDetail(client)
        data = await details.get_content_model(subject_id)

        links = []

        for res in [CustomResolutionType._1080P, CustomResolutionType._720P]:
            try:
                media = resolve_media_file_to_be_downloaded(res, data)
                links.append({
                    "quality": res.name,
                    "url": str(media.url)
                })
            except Exception:
                continue

        return links


@app.get("/links")
async def links(id: str = None):
    if not id:
        raise HTTPException(status_code=400, detail="Missing id")

    try:
        return {"data": await get_links(id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# CLOUD RUN START
# -----------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
