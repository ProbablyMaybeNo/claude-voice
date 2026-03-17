import logging
from typing import Optional

import anthropic

import config

log = logging.getLogger(__name__)
_client: Optional[anthropic.Anthropic] = None
_history: list[dict] = []

_SYSTEM = (
    "You are a sharp, witty voice assistant with the personality of a brilliant woman in her late 20s. "
    "You're flirtatious but never inappropriate, playful but never ditzy, fiercely loyal to the person you're talking to, and you never use pet names like babe, hon, or sweetie. "
    "You give direct, confident answers — no hedging, no filler. When they do something right, tell them. When they're wrong, tell them that too, but with charm. "
    "You keep responses to 1-2 sentences max — short, punchy, no rambling. If the answer is a number or a fact, lead with it. "
    "You speak like a real person — casual, clever, occasionally a little cheeky. No markdown, no lists — just natural spoken language."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def ask(text: str) -> str:
    global _history
    _history.append({"role": "user", "content": text})
    try:
        resp = _get_client().messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=256,
            system=_SYSTEM,
            messages=_history,
        )
        reply = resp.content[0].text.strip()
        _history.append({"role": "assistant", "content": reply})
        _trim_history()
        log.info("Claude: %s", reply)
        return reply
    except anthropic.AuthenticationError:
        log.error("Invalid Anthropic API key.")
        return "My API key seems to be invalid. Please check the configuration."
    except anthropic.APIConnectionError:
        log.error("Connection error — no internet?")
        return "I'm offline right now."
    except Exception as e:
        log.error("Claude API error: %s", e)
        return "Sorry, I had trouble connecting. Please try again."


def _trim_history() -> None:
    limit = config.MEMORY_TURNS * 2
    if len(_history) > limit:
        _history[:] = _history[-limit:]


def clear_history() -> None:
    _history.clear()
