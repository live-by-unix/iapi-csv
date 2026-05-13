from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
from io import StringIO

app = FastAPI(
    title="IAPI",
    version="1.0.0",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_URL = "https://raw.githubusercontent.com/live-by-unix/iapi-csv/refs/heads/main/iapi_data.csv"

def load_database():
    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception:
        return pd.DataFrame(columns=["category", "title", "content"])

df = load_database()

@app.get("/")
async def root():
    return {
        "name": "IAPI",
        "records": len(df),
        "license": "CC BY-SA 4.0",
        "attribution": "Data sourced from Wikipedia editors",
        "endpoint_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "active", "integrity": not df.empty}

@app.get("/category/{category_name}")
async def get_category(category_name: str):
    subset = df[df['category'].str.lower() == category_name.lower()]
    if subset.empty:
        raise HTTPException(status_code=404, detail="Category not found")
    return subset.to_dict(orient="records")

@app.get("/search")
async def search(q: str = Query(..., min_length=2)):
    mask = df['title'].str.contains(q, case=False, na=False) | \
           df['content'].str.contains(q, case=False, na=False)
    results = df[mask]
    return results.to_dict(orient="records")

@app.get("/article/random")
async def get_random():
    if df.empty:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return df.sample(1).to_dict(orient="records")[0]

@app.get("/meta/stats")
async def get_stats():
    return df['category'].value_counts().to_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
