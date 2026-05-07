"""GPT-4o-mini wrapper used by Celery tasks (Layer 4) and live AI tip emitter."""
from __future__ import annotations

import asyncio
import os
from typing import Optional


async def gpt_4o_mini(prompt: str, *, timeout: float = 12.0, system: Optional[str] = None) -> str:
    """Best-effort GPT-4o-mini call via emergentintegrations or OpenAI direct.
    Returns empty string if not configured (caller must fall back).
    """
    key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return ""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore
        chat = LlmChat(
            api_key=key,
            session_id=f"task-{abs(hash(prompt)) % 10_000_000}",
            system_message=system or "You are a professional Indian grassroots football analyst.",
        ).with_model("openai", "gpt-4o-mini")
        resp = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=timeout)
        return (resp or "").strip()
    except Exception:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system or "Football analyst."},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 220,
                    },
                )
                r.raise_for_status()
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
        except Exception:
            return ""
