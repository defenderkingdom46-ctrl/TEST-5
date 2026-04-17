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
# HEALTH CHECK
# -----------------------
@app.get("/")
def home():
    return {"status": "MovieBox API ready"}


# -----------------------
# TMDB SEARCH (USER INPUT)
# -----------------------
def tmdb_search(query):
    res = requests.get(TMDB_URL, params={
        "api_key": TMDB_API_KEY,
        "query": query
    })
    return res.json().get("results", [])


# -----------------------
# MOVIEBOX AUTO FIND (NO SEARCH MODULE)
# -----------------------
async def find_moviebox_id(title):
    """
    IMPORTANT:
    We avoid broken moviebox_api.search module.
    Instead we rely on internal content scan.
    """

    async with MovieBoxHttpClient() as client:
        # fallback approach: try content lookup via detail fetch
        details = DownloadableFilesDetail(client)

        # brute-force safe approach using internal dataset
        data = await details.get_content_model(title)

        # try to extract id safely
        if hasattr(data, "id"):
            return {
                "id": data.id,
                "title": getattr(data, "title", title)
            }

        return None


# -----------------------
# MAIN SEARCH → LINKS FLOW
# -----------------------
@app.get("/search")
async def search(query: str = None):
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    try:
        # 1. TMDB search
        tmdb_results = tmdb_search(query)

        if not tmdb_results:
            return {"error": "No results found"}

        best = tmdb_results[0]
        title = best.get("title")

        # 2. MovieBox resolve (NO BROKEN SEARCH MODULE)
        mb = await find_moviebox_id(title)

        if not mb:
            return {"error": "MovieBox match not found"}

        # 3. directly fetch links
        links = await get_links(mb["id"])

        return {
            "title": mb["title"],
            "id": mb["id"],
            "links": links
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# LINKS FETCHER
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


# -----------------------
# STARTUP
# -----------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
