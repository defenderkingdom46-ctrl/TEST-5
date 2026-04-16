from fastapi import FastAPI, HTTPException
import os

from moviebox_api.v3.http_client import MovieBoxHttpClient
from moviebox_api.v3.core import DownloadableFilesDetail
from moviebox_api.v3.download import resolve_media_file_to_be_downloaded
from moviebox_api.v3.constants import CustomResolutionType

app = FastAPI()


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


@app.get("/")
def home():
    return {"status": "MovieBox API running"}


@app.get("/links")
async def links(id: str = None):
    if not id:
        raise HTTPException(status_code=400, detail="Missing id")

    try:
        result = await get_links(id)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Cloud Run compatible startup
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)