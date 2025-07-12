import os
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

class Query(BaseModel):
    question: str

async def google_search(query: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": 3,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None
            first = items[0]
            title = first.get("title", "")
            snippet = first.get("snippet", "")
            link = first.get("link", "")
            return {"title": title, "snippet": snippet, "link": link}
        else:
            raise Exception(f"Google API error: {resp.status_code}")

async def duckduckgo_search(query: str):
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
        "skip_disambig": 1
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("Abstract", "")
            abstract_url = data.get("AbstractURL", "")
            heading = data.get("Heading", "")
            if abstract:
                return {"title": heading, "snippet": abstract, "link": abstract_url}
            else:
                return None
        else:
            raise Exception(f"DuckDuckGo API error: {resp.status_code}")

@app.post("/search")
async def search(request: Request, query: Query):
    q = query.question
    try:
        result = await google_search(q)
        if not result:
            result = await duckduckgo_search(q)
        source = "Google"
    except Exception:
        try:
            result = await duckduckgo_search(q)
            source = "DuckDuckGo"
        except Exception:
            return {"error": "Both search providers failed."}

    if not result:
        return {"error": "No results found."}

    answer = (
    f"أنا مش مختص، لكن لقيت ليك معلومة من {source}:\n\n"
    f"📌 **{result['title']}**\n"
    f"{result['snippet']}\n\n"
    f"🔗 [اقرأ المصدر]({result['link']})"
    )

    return {"answer": answer}
