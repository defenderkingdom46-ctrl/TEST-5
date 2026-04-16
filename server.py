from fastapi import FastAPI, HTTPException
import os
import requests

from moviebox_api.v3.http_client import MovieBoxHttpClient
from moviebox_api.v3.core import DownloadableFilesDetail
from moviebox_api.v3.download import resolve_media_file_to_be_downloaded
from moviebox_api.v3.constants import CustomResolutionType

app = FastAPI()

TMDB_API_KEY = "e1d304dda8b47424245c3c62fe9baea2"
TMDB_URL = "https://api.themoviedb.org/3/search/movie"


# -----------------------
# TMDB SEARCH
# -----------------------
def tmdb_search(query):
    res = requests.get(TMDB_URL, params={
        "api_key": TMDB_API_KEY,
        "query": query
    })
    data = res.json()
    return data.get("results", [])


# -----------------------
# MOVIEBOX SEARCH (IMPORTANT PART)
# -----------------------
async def moviebox_search(title):
    async with MovieBoxHttpClient() as client:
        # using internal search method from library if available
        from moviebox_api.v3.search import search

        results = await search(client, title)

        for item in results:
            return {
                "id": getattr(item, "id", None),
                "title": getattr(item, "title", title)
            }

    return None


# -----------------------
# RESOLVE (NEW MAPPING LAYER)
# -----------------------
@app.get("/resolve")
async def resolve(query: str = None):
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    try:
        # 1. TMDB search
        tmdb_results = tmdb_search(query)

        if not tmdb_results:
            return {"error": "No TMDB results"}

        best = tmdb_results[0]
        title = best.get("title")

        # 2. MovieBox search using TITLE (NOT TMDB ID)
        mb = await moviebox_search(title)

        if not mb:
            return {"error": "No MovieBox match"}

        return mb

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# LINKS
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
            except:
                continue

        return links


@app.get("/links")
async def links(id: str = None):
    if not id:
        raise HTTPException(status_code=400, detail="Missing id")

    return {"data": await get_links(id)}


# -----------------------
# HEALTH
# -----------------------
@app.get("/")
def home():
    return {"status": "MovieBox API + TMDB mapping running"}


# -----------------------
# STARTUP
# -----------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
