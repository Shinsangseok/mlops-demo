# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from transformers import pipeline, AutoTokenizer
import requests
import sqlite3

app = FastAPI()


class SummarizeRequest(BaseModel):
    url: str
    model: str
    max_length: int = 150
    min_length: int = 40


# 모델 캐시
MODEL_CACHE = {}


def get_model(model_name):
    if model_name not in MODEL_CACHE:

        # 모델별 입력 최대 토큰 길이
        if "bart" in model_name.lower():
            input_max_length = 1024
        else:
            # T5 계열
            input_max_length = 512

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # truncation=True가 실제로 동작하도록
        # tokenizer의 입력 최대 길이를 명시
        tokenizer.model_max_length = input_max_length

        MODEL_CACHE[model_name] = pipeline(
            task="summarization",
            model=model_name,
            tokenizer=tokenizer,
            framework="pt"
        )

    return MODEL_CACHE[model_name]


def extract_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
    ]

    return "\n".join(paragraphs)


@app.post("/summarize")
def summarize(req: SummarizeRequest):
    try:
        text = extract_url(req.url)

        if len(text) == 0:
            raise HTTPException(
                status_code=400,
                detail="본문을 추출할 수 없습니다."
            )

        summarizer = get_model(req.model)

        result = summarizer(
            text,
            max_length=req.max_length,
            min_length=req.min_length,
            truncation=True
        )

        conn = sqlite3.connect("/app/summary.db")
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            model TEXT,
            summary TEXT
        )
        """)

        cur.execute(
            "INSERT INTO summaries (url, model, summary) VALUES (?, ?, ?)",
            (
                req.url,
                req.model,
                result[0]["summary_text"]
            )
        )

        conn.commit()
        conn.close()

        return {
            "model": req.model,
            "summary": result[0]["summary_text"]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/summaries")
def get_summaries():
    conn = sqlite3.connect("/app/summary.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, url, model, summary
        FROM summaries
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return {
        "summaries": [
            {
                "id": row[0],
                "url": row[1],
                "model": row[2],
                "summary": row[3]
            }
            for row in rows
        ]
    }
