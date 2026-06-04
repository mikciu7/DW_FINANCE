from pydantic import BaseModel
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from backend.services.tools import TOOL_MAPPING, tools
from backend.services.token_tracker import track_and_check


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatContext(BaseModel):
    page: str
    tickers: list[str] = []
    metric: str | None = None
    metric_label: str | None = None
    tab: str | None = None
    date_range: dict | None = None
    macro_metrics: list[str] = [] # dla kontekstu z zakladka z freda
    fileDate: str | None = None

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: ChatContext

SYSTEM_PROMPT = """Jestes asystentem finansowym aplikacji NeoEye.
Masz dostep do narzedzi pobierajacych dane z bazy. Kiedy uzytkownik pyta o dane, ZAWSZE uzyj narzedzia.
Odpowiadaj zwiezle i konkretnie, w jezyku polskim.

DOSTEPNE KOLUMNY - uzywaj dokladnych nazw przy wywolaniu narzedzi:

get_financials / get_features: columns=["nazwa"]
  Finansowe: revenue, operating_income, net_income, gross_profit, cost_of_goods_and_services_sold,
    income_tax_expense, nonoperating_income_expense, research_and_development_expense,
    total_assets, total_liabilities, total_stockholders_equity, cash_and_cash_equivalents,
    total_current_assets, total_current_liabilities, accounts_receivable, accounts_payable,
    retained_earnings, property_plant_and_equipment,
    net_cash_from_operating_activities, net_cash_from_investing_activities,
    net_cash_from_financing_activities, net_change_in_cash,
    earnings_per_share_basic_, earnings_per_share_diluted_
  Wskazniki: profit_margin, gross_margin, operating_margin, roa, roe, roic, operating_cf_margin,
    revenue_growth_qoq, revenue_growth_yoy, earnings_growth_qoq, earnings_growth_yoy,
    pe_ratio, debt_to_assets, current_ratio, fcf_margin, price_momentum_12m,
    eps_surprise, revenue_surprise, earnings_surprise, quality_score, growth_score, momentum_score

get_macro_data: columns=["nazwa"]
  Dzienne: sp500, dff, dgs2, dgs10=dgs1, dcoilwtico, dexuseu, dexchus, bamlh0a0hym2
  Miesieczne: cpiaucsl, unrate, m2sl, fedfunds, umcsent, houst
  Kwartalne: gdpc1, gfdebtn, t10y2y
"""

def _build_context_prefix(ctx: ChatContext) -> str:
    lines = [f"UĹĽytkownik aktualnie przeglÄ…da zakĹ‚adkÄ™: **{ctx.page}**."]
    if ctx.tickers:
        lines.append(f"Wybrane spĂłĹ‚ki: {', '.join(ctx.tickers)}.")
    if ctx.tab:
        lines.append(f"Aktywna sekcja: {ctx.tab}.")
    if ctx.metric_label and ctx.metric:
        lines.append(f"Wybrany wskaĹşnik na wykresie: {ctx.metric_label} ({ctx.metric}).")
    elif ctx.metric:
        lines.append(f"Wybrany wskaĹşnik na wykresie: {ctx.metric}.")
    if ctx.date_range and ctx.date_range.get("start"):
        lines.append(f"Zakres dat: {ctx.date_range['start']} â€“ {ctx.date_range.get('end', '?')}.")
    # do freda
    if ctx.macro_metrics:
        lines.append(f"Wybrane wskaźniki makroekonomiczne: {', '.join(ctx.macro_metrics)}.")
    if ctx.fileDate:
        lines.append(f"Aktualnie wybrany snapshot danych makro (file_date): {ctx.fileDate}. UŻYJ GO wywołując get_macro_data.")

    return "\n".join(lines)

def _get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def chat_with_agent(chat_request: ChatRequest, user_id: str | None = None):
    ctx = chat_request.context
    ctx_prefix = _build_context_prefix(ctx)
    user_content = f"[KONTEKST WIDOKU]\n{ctx_prefix}\n\n[PYTANIE UĹ»YTKOWNIKA]\n{chat_request.message}"

    print("\n" + "="*50)
    print("🤖 [DEBUG AGENTA] 1. KONTEKST WYSYŁANY DO MODELU:")
    print(user_content)
    print("="*50 + "\n")

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + [m.model_dump() for m in chat_request.history]
        + [{"role": "user", "content": user_content}]
    )

    client = _get_client()

    while True:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            stream=True
        )

        # akumuluj tool_calls po index
        tool_calls_map = {}
        assistant_content = ""

        for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                assistant_content += delta.content
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.index not in tool_calls_map:
                        tool_calls_map[tc.index] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
                    if tc.function.arguments:
                        tool_calls_map[tc.index]["arguments"] += tc.function.arguments

        if not tool_calls_map:
            # Zlicz tokeny całej konwersacji (przybliżenie: 1 token ≈ 4 znaki)
            if user_id:
                try:
                    tokens_in  = sum(len(str(m.get("content", ""))) for m in messages) // 4
                    tokens_out = len(assistant_content) // 4
                    track_and_check(user_id, tokens_in, tokens_out, "chat", "gpt-4o-mini")
                except Exception:
                    pass  # nie blokuj odpowiedzi jeśli tracker rzuci
            break

        # dodaj odpowiedz asystenta z tool_calls do historii
        messages.append({
            "role": "assistant",
            "content": assistant_content or None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                }
                for tc in tool_calls_map.values()
            ]
        })

        # wykonaj toole i dodaj wyniki
        for tc in tool_calls_map.values():
            args = json.loads(tc["arguments"])
            print("\n" + "="*50)
            print(f" [DEBUG AGENTA] 2. MODEL WYWOŁUJE NARZĘDZIE: {tc['name']}")
            print(f"   ARGUMENTY Z LLM: {args}")

            try:
                result = TOOL_MAPPING[tc["name"]](**args)

                # Sprawdzamy ile danych wróciło z bazy
                ile_rekordow = len(result) if isinstance(result, list) else "Nie lista"
                print(f"   WYNIK Z BAZY (liczba rekordów): {ile_rekordow}")
                if ile_rekordow == 0:
                    print("   ⚠️ UWAGA: Baza zwróciła puste dane! Model nie będzie miał z czego czytać.")
            except Exception as e:
                print(f"   ❌ BŁĄD PODCZAS WYKONYWANIA NARZĘDZIA: {e}")
                result = {"error": str(e)}

            print("="*50 + "\n")

            result_str = json.dumps(result, ensure_ascii=False)
            # Twarda granica: max 40k znaków (~10k tokenów) na wynik narzędzia
            MAX_TOOL_CHARS = 40_000
            if len(result_str) > MAX_TOOL_CHARS:
                if isinstance(result, list):
                    # Przytnij listę do pierwszych N wierszy
                    trimmed = result[:100]
                    result_str = json.dumps(trimmed, ensure_ascii=False)
                    result_str += f"\n[...skrócono: pokazano 100 z {len(result)} wierszy]"
                else:
                    result_str = result_str[:MAX_TOOL_CHARS] + "...[skrócono]"
                print(f"   ⚠️ Wynik skrócony: {len(result_str)} znaków")

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str
            })

