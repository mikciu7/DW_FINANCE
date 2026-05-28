from pydantic import BaseModel
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from backend.services.tools import TOOL_MAPPING, tools
from tools import TOOL_MAPPING, tools

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatContext(BaseModel):
    page: str
    tickers: list[str]

class ChatRequest(BaseModel):
    messages: list[str]
    history: list[ChatMessage] = []
    context: ChatContext

SYSTEM_PROMPT = """Jesteś asystentem finansowym, który pomaga użytkownikowi znaleźć informacje o spółkach giełdowych.
Odpowiadaj na pytania dotyczące spółek, ich tickerów, wskazników finansowych, aktualnych wydarzeń i innych informacji związanych z rynkiem kapitałowym.Odpowiadaj w języku Polskim"""

def _get_client():
    validation_key = os.getenv("OPENROUTER_API_KEY", "")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=validation_key,
        default_headers={
            "HTTP-Referer": "http://13.63.209.239/",
            "X-Title": "NeoEye"
        }
    )

def chat_with_agent(chat_request: ChatRequest):
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + [m.model_dump() for m in chat_request.history]
        + [{"role": "user", "content": chat_request.messages[0]}]
        + [{"role": "user", "content": chat_request.context.page}]
    )

    client = _get_client()

    while True:
        stream = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
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

