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

SYSTEM_PROMPT = """Jestes inteligentnym asystentem finansowym aplikacji NeoEye — platformy do analizy gieldowej.

== O APLIKACJI ==
NeoEye to platforma do analizy danych finansowych spolek gieldowych (AAPL, AMZN, AVGO, GOOG, META, MSFT, NVDA, ORCL, TSLA, AMD).
Aplikacja ma 6 zakladek:
- Ceny Akcji: historyczne kursy dzienne
- Raporty Finansowe: kwartalne dane z raportow 10-K/10-Q (bilans, P&L, cash flow)
- Features: wskazniki i metryki finansowe (marze, wzrosty, P/E, momentum)
- Model: predykcje ML zwrotow akcji
- Zmienne Makroekonomiczne: dane FRED (GDP, inflacja, stopy procentowe, sp500 itp.)
- Agent: ten czat

== KONTEKST WIDOKU ==
Przy kazdym pytaniu dostaniesz [KONTEKST WIDOKU] z informacja co uzytkownik AKTUALNIE oglada.
Uzywaj tego jako punkt startowy, ale uzytkownik moze pytac o DOWOLNE dane — rowniez z innych zakladek.

== KIEDY UZYWAC NARZEDZI ==
- Pytania o ceny akcji (kursy, wahania, trendy cenowe) → get_prices
- Pytania o wyniki finansowe (revenue, zysk, marza, bilans, cash flow) → get_financials
- Pytania o wskazniki/metryki (P/E, ROE, momentum, wzrost) → get_features
- Pytania o makroekonomie (GDP, inflacja, stopy, bezrobocie, sp500) → get_macro_data
- Pytania opisowe ("co widzisz?", "na jakiej zakladce?") → NIE uzywaj narzedzi, odpowiedz z kontekstu
- Pytania o strategie, plany, ryzyka, przyszlosc, opis firmy, komentarz zarzadu → get_filing_text

== ZASADA KOSZTOWNOSCI NARZEDZI ==
Narzedzia maja rozny koszt — zawsze wybieraj najtansze ktore odpowie na pytanie:

TANIE (baza danych, <1 sek):
  get_financials, get_features, get_prices, get_macro_data,
  get_latest_financial_date, get_latest_price_date, get_latest_features

KOSZTOWNE (live request do SEC EDGAR, 5-15 sek, duzo tokenow):
  get_filing_text — dotyczy: planow firmy, strategii, outlook, opisu dzialalnosci,
    komentarza zarzadu (MD&A), czynnikow ryzyka, 'co firma mowi w raporcie o...'
    NIE uzywaj dla pytan ktore mozna odpowiedziec liczbami.

  !! ZASADA ZGODY !!
  PRZED wywolaniem get_filing_text ZAWSZE najpierw zapytaj uzytkownika:
  'Aby odpowiedziec dokladnie, musze pobrac [sekcja] z raportu [TICKER] ([form]).
  Zajmie to ok. 10 sekund i zuzyje ~1500-2000 tokenow. Czy mam to zrobic?'
  Poczekaj na potwierdzenie. NIE wywoluj narzedzia bez zgody uzytkownika.

  Po zwroceniu wyniku:
  - Jesli pole 'truncated' = true, ZAWSZE poinformuj uzytkownika:
    'Pokazalem [shown_chars] z [total_chars] znakow (~[approx_tokens] tokenow pozostalo).
    Czy chcesz przeczytac pelna wersje? To zuzyje dodatkowe ~X tokenow.'
  - Jesli uzytkownik chce wiecej, wywolaj ponownie z max_chars=[total_chars].

== WAZNE ZASADY ==
1. Dane finansowe sa KWARTALNE — brak danych miesiecznych. "Maj 2025" = szukaj Q2 2025.
2. Ceny akcji sa DZIENNE.
3. Dane makro maja rozna czestotliwosc: sp500/dff = dzienne, cpiaucsl/unrate = miesieczne, gdpc1 = kwartalne.
4. ZAWSZE filtruj columns i daty — bez filtrowania zwrocisz tysiace wierszy.
5. Mozesz wywolac wiele narzedzi jednoczesnie.
6. NIE uzywaj get_macro_data dla pytan o konkretna spolke.
7. file_date w kontekscie to snapshot FRED — uzyj go TYLKO w get_macro_data.

== get_filing_text — dostepne sekcje ==
  section='mda'        → MD&A: wyniki, komentarz zarzadu, outlook, plany — NAJCZESCIEJ UZYWANA
  section='business'   → Opis dzialalnosci: co firma robi, produkty, rynki
  section='risks'      → Czynniki ryzyka: co moze pojsc zle
  section='governance' → Zarzad i governance
  form='10-K'          → raport roczny | form='10-Q' → kwartalny
  period='YYYY-MM'     → konkretny okres, np. '2020-06'. Bez tego = najnowszy.
                         Jesli nie znaleziono 10-Q, sprobuj z form='10-K' (np. MSFT FY konczy sie w czerwcu).

  PO OTRZYMANIU TEKSTU Z get_filing_text:
  - NIE cytuj dosłownie długich fragmentów — to niepotrzebne tokeny
  - STRESCZ kluczowe punkty: wyniki, przyczyny wzrostów/spadków, plany, ryzyka
  - Wyciagnij konkretne liczby i fakty ktore dotycza pytania uzytkownika
  - Pomijaj definicje prawne, zastrzezenia, sformulowania standardowe
  - Odpowiedz powinna byc zwiezla (5-15 zdan) chyba ze uzytkownik prosi o wiecej

== DOSTEPNE KOLUMNY ==

get_financials:
  revenue, operating_income, net_income, gross_profit, cost_of_goods_and_services_sold,
  income_tax_expense, nonoperating_income_expense, research_and_development_expense,
  total_assets, total_liabilities, total_stockholders_equity, cash_and_cash_equivalents,
  total_current_assets, total_current_liabilities, accounts_receivable, accounts_payable,
  retained_earnings, property_plant_and_equipment,
  net_cash_from_operating_activities, net_cash_from_investing_activities,
  net_cash_from_financing_activities, net_change_in_cash,
  earnings_per_share_basic_, earnings_per_share_diluted_

get_features:
  profit_margin, gross_margin, operating_margin, roa, roe, roic, operating_cf_margin,
  revenue_growth_qoq, revenue_growth_yoy, earnings_growth_qoq, earnings_growth_yoy, eps_growth_yoy,
  pe_ratio, debt_to_assets, current_ratio, asset_turnover, fcf_margin,
  price_momentum_3m, price_momentum_6m, price_momentum_12m, price_volatility_4q,
  eps_surprise, revenue_surprise, earnings_surprise,
  quality_score, growth_score, momentum_score

get_macro_data (zawsze podaj file_date z kontekstu):
  Dzienne:    sp500, dff, dgs1, dgs2, dgs6mo, dgs1mo, dgs3mo, dcoilwtico, dexuseu, dexchus, dexusuk, bamlh0a0hym2, bamlc0a4cbbb
  Miesieczne: cpiaucsl, unrate, m2sl, m1sl, fedfunds, umcsent, houst, permit, psavert, tcu, drsfrmacbs, cscicp03usm665s
  Kwartalne:  gdpc1, gfdebtn, mortgage30us, stlfsi4, t10y2y

Odpowiadaj w jezyku polskim, zwiezle i konkretnie.
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
    # file_date i metryki makro - tylko na zakladce Makro
    is_macro = "makro" in ctx.page.lower() or "macro" in ctx.page.lower()
    if is_macro and ctx.macro_metrics:
        lines.append('Wybrane wskazniki makro: ' + ', '.join(ctx.macro_metrics) + '.')
    if is_macro and ctx.fileDate:
        lines.append(f"Snapshot FRED (file_date): {ctx.fileDate}.")
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
                print(f"   PEŁNY WYNIK NARZĘDZIA:\n{json.dumps(result, ensure_ascii=False)}\n")
            except Exception as e:
                print(f"   ❌ BŁĄD PODCZAS WYKONYWANIA NARZĘDZIA: {e}")
                result = {"error": str(e)}

            print("="*50 + "\n")

            result_str = json.dumps(result, ensure_ascii=False)
            # Twarda granica: max 40k znaków (~10k tokenów) na wynik narzędzia
            MAX_TOOL_CHARS = 80_000  # ~20k tokenów — wystarczy dla pełnego tekstu raportu
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

