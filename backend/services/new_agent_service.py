from pydantic import BaseModel
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from backend.services.tools import TOOL_MAPPING, tools


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

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: ChatContext

SYSTEM_PROMPT = """Jesteś asystentem finansowym aplikacji NeoEye, który pomaga użytkownikowi analizować dane giełdowe.
Masz dostęp do narzędzi pozwalających pobierać dane finansowe, ceny akcji i wskaźniki z bazy danych.
Kiedy użytkownik pyta o dane, ZAWSZE użyj odpowiedniego narzędzia zamiast odpowiadać z pamięci.
Odpowiadaj zwięźle i konkretnie, w języku polskim."""

def _build_context_prefix(ctx: ChatContext) -> str:
    lines = [f"Użytkownik aktualnie przegląda zakładkę: **{ctx.page}**."]
    if ctx.tickers:
        lines.append(f"Wybrane spółki: {', '.join(ctx.tickers)}.")
    if ctx.tab:
        lines.append(f"Aktywna sekcja: {ctx.tab}.")
    if ctx.metric_label and ctx.metric:
        lines.append(f"Wybrany wskaźnik na wykresie: {ctx.metric_label} ({ctx.metric}).")
    elif ctx.metric:
        lines.append(f"Wybrany wskaźnik na wykresie: {ctx.metric}.")
    if ctx.date_range and ctx.date_range.get("start"):
        lines.append(f"Zakres dat: {ctx.date_range['start']} – {ctx.date_range.get('end', '?')}.")
    return "\n".join(lines)

def _get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def chat_with_agent(chat_request: ChatRequest):
    ctx = chat_request.context
    ctx_prefix = _build_context_prefix(ctx)
    user_content = f"[KONTEKST WIDOKU]\n{ctx_prefix}\n\n[PYTANIE UŻYTKOWNIKA]\n{chat_request.message}"

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

