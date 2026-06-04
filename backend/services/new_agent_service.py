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

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: ChatContext

SYSTEM_PROMPT = """JesteĹ› asystentem finansowym aplikacji NeoEye, ktĂłry pomaga uĹĽytkownikowi analizowaÄ‡ dane gieĹ‚dowe.
Masz dostÄ™p do narzÄ™dzi pozwalajÄ…cych pobieraÄ‡ dane finansowe, ceny akcji i wskaĹşniki z bazy danych.
Kiedy uĹĽytkownik pyta o dane, ZAWSZE uĹĽyj odpowiedniego narzÄ™dzia zamiast odpowiadaÄ‡ z pamiÄ™ci.
Odpowiadaj zwiÄ™Ĺşle i konkretnie, w jÄ™zyku polskim."""

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
    if ctx.macro_metrics:
        lines.append(f"Wybrane wskaźniki makroekonomiczne: {', '.join(ctx.macro_metrics)}.")

    return "\n".join(lines)

def _get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def chat_with_agent(chat_request: ChatRequest, user_id: str | None = None):
    ctx = chat_request.context
    ctx_prefix = _build_context_prefix(ctx)
    user_content = f"[KONTEKST WIDOKU]\n{ctx_prefix}\n\n[PYTANIE UĹ»YTKOWNIKA]\n{chat_request.message}"

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
            print(tc)
            result = TOOL_MAPPING[tc["name"]](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False)
            })

