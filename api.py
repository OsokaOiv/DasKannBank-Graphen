from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data import (
    load_categories,
    load_transactions,
    prepare_expenses,
    prepare_income,
    prepare_profit_loss,
)
from constants import CATEGORIES_FILE

app = FastAPI(title="DKB Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(df):
    if df.empty:
        return []
    return df.fillna(0).to_dict(orient="records")


def _convert_dates(records, date_fields=None):
    if date_fields is None:
        date_fields = ["Datum", "Monat"]
    for rec in records:
        for field in date_fields:
            if field in rec and rec[field] is not None:
                if hasattr(rec[field], "isoformat"):
                    rec[field] = rec[field].isoformat()
    return records


def _build_response():
    categories = load_categories(CATEGORIES_FILE)
    df = load_transactions()
    if df.empty:
        return {"expenses": [], "income": [], "profit_loss": [], "categories": list(categories.keys())}

    expenses = prepare_expenses(df, categories)
    expenses["Monat_Label"] = expenses["Monat"].dt.strftime("%b %Y")
    income = prepare_income(df)
    profit_loss = prepare_profit_loss(expenses, income)

    exp_data = _convert_dates(_serialize(expenses))
    inc_data = _convert_dates(_serialize(income))
    pl_data = _convert_dates(_serialize(profit_loss))

    return {
        "expenses": exp_data,
        "income": inc_data,
        "profit_loss": pl_data,
        "categories": sorted(expenses["Kategorie"].unique().tolist()) if not expenses.empty else [],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/data")
def get_data():
    return _build_response()


@app.post("/api/upload")
async def upload_csv(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Nur CSV-Dateien erlaubt")
    csv_dir = Path("csv")
    csv_dir.mkdir(exist_ok=True)
    content = await file.read()
    (csv_dir / file.filename).write_bytes(content)
    return {"saved": file.filename}
