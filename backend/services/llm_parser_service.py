import json
import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Wymuszenie załadowania zmiennych środowiskowych!
load_dotenv()

def _get_client():
    return OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )

def parse_pre2010(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for _, row in df.iterrows():
        parsed = _parse_single(row.to_json())
        if not parsed.empty:
            for col in df.columns:
                if col not in parsed.columns:
                    parsed[col] = row[col]
            results.append(parsed.iloc[0])
        else:
            results.append(row)
    return pd.DataFrame(results, columns=df.columns)

def _parse_single(text_content: str, proba=1) -> pd.DataFrame:
    MAKS_PROB = 3
    expected_keys = [
        "revenue", "cost_of_goods_and_services_sold", "gross_profit",
        "operating_income", "net_income", "total_assets",
        "total_liabilities", "retained_earnings",
        "net_cash_from_operating_activities", "net_change_in_cash"
    ]
    system_prompt = f"""You are a financial data extractor.
Extract values for these keys: {expected_keys}.
All final numbers MUST be in MILLIONS.
Return ONLY a valid JSON object. Use null for missing values.
No currency symbols, no commas."""

    try:
        klucz = os.getenv("OPENROUTER_API_KEY", "")
        if not klucz:
            print("[llm_parser] Błąd: Brak klucza OPENROUTER_API_KEY w pliku .env!")
            return pd.DataFrame()

        # Zmiana na szybszy, stabilniejszy model
        response = _get_client().chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract financial data:\n\n{text_content[:15000]}"}
            ],
            temperature=0.1,
        )
        
        # Zabezpieczenie przed pustą odpowiedzią serwera
        if not response or not hasattr(response, 'choices') or not response.choices:
            if proba < MAKS_PROB:
                time.sleep(2)
                return _parse_single(text_content, proba + 1)
            print("[llm_parser] Błąd API OpenRouter: Serwer przeciążony po 3 próbach.")
            return pd.DataFrame()

        content = response.choices[0].message.content.strip()
        if "```" in content:
            # Ulepszone czyszczenie bloków kodu (czasami model pisze ```json, czasami samo ```)
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
                
        data = json.loads(content.strip())
        for key in data:
            if isinstance(data[key], (int, float)) and data[key] > 1_000_000:
                data[key] = data[key] / 1_000_000
        return pd.DataFrame([data])
        
    except Exception as e:
        if proba < MAKS_PROB:
            time.sleep(2)
            return _parse_single(text_content, proba + 1)
        print(f"[llm_parser] Błąd AI po {MAKS_PROB} próbach: {e}")
        return pd.DataFrame()