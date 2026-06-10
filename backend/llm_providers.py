"""
Hybrid LLM provider.

Router LLM      → always local Ollama (fast, small model — routing + rewriting only)
Answer LLM      → Claude when ANTHROPIC_API_KEY set, else any chosen Ollama model

Environment variables:
  ANTHROPIC_API_KEY    — Anthropic key (activates Claude for final answers)
  LLM_PROVIDER         — "auto" (default) | "anthropic" | "ollama"
  ANTHROPIC_MODEL      — default: claude-sonnet-4-6
  OLLAMA_ROUTER_MODEL  — default: llama3   (fast, for routing/rewriting)
  OLLAMA_ANSWER_MODEL  — default: llama3   (can be gemma3:12b, mistral, etc.)
"""

import os
import requests

from langchain_ollama import ChatOllama

try:
    from langchain_anthropic import ChatAnthropic
    _ANTHROPIC_PKG = True
except ImportError:
    _ANTHROPIC_PKG = False


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL",      "http://localhost:11434")
OLLAMA_ROUTER_MODEL  = os.getenv("OLLAMA_ROUTER_MODEL",  os.getenv("OLLAMA_MODEL", "llama3"))
OLLAMA_ANSWER_MODEL  = os.getenv("OLLAMA_ANSWER_MODEL",  os.getenv("OLLAMA_MODEL", "llama3"))
ANTHROPIC_MODEL      = os.getenv("ANTHROPIC_MODEL",      "claude-sonnet-4-6")
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY",    "")
LLM_PROVIDER         = os.getenv("LLM_PROVIDER",         "auto")  # auto | anthropic | ollama


# ─────────────────────────────────────────────────────────────────────────────
# Ollama model discovery
# ─────────────────────────────────────────────────────────────────────────────

def list_ollama_models() -> list[dict]:
    """Return models available in the local Ollama instance."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [
            {
                "name": m["name"],
                "size_gb": round(m.get("size", 0) / 1e9, 1),
            }
            for m in models
        ]
    except Exception as e:
        print(f"[LLM] Could not reach Ollama: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Router LLM — always local, small/fast, only used for routing + rewriting
# ─────────────────────────────────────────────────────────────────────────────

router_llm = ChatOllama(model=OLLAMA_ROUTER_MODEL)
print(f"[LLM] Router  → Ollama ({OLLAMA_ROUTER_MODEL})")


# ─────────────────────────────────────────────────────────────────────────────
# Provider resolution
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_provider() -> str:
    if LLM_PROVIDER == "ollama":
        return "ollama"
    if LLM_PROVIDER == "anthropic":
        if not _ANTHROPIC_PKG:
            raise RuntimeError("langchain-anthropic not installed. Run: pip install langchain-anthropic")
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        return "anthropic"
    # auto: use Claude if key present, else Ollama
    if _ANTHROPIC_PKG and ANTHROPIC_API_KEY:
        return "anthropic"
    return "ollama"


# ─────────────────────────────────────────────────────────────────────────────
# Answer LLM — can be swapped at runtime via swap_answer_model()
# ─────────────────────────────────────────────────────────────────────────────

# Mutable container so swap_answer_model() affects all callers via this module
_state = {
    "answer_model": OLLAMA_ANSWER_MODEL,  # current Ollama model name (only used when provider=ollama)
}


def _build_answer_llm(ollama_model: str | None = None):
    provider = _resolve_provider()
    if provider == "anthropic":
        print(f"[LLM] Answer  → Claude ({ANTHROPIC_MODEL})")
        return ChatAnthropic(
            model=ANTHROPIC_MODEL,
            api_key=ANTHROPIC_API_KEY,
            max_tokens=4096,
            streaming=True,
        )
    model = ollama_model or _state["answer_model"]
    print(f"[LLM] Answer  → Ollama ({model})")
    return ChatOllama(model=model)


answer_llm = _build_answer_llm()


def swap_answer_model(model_name: str) -> dict:
    """
    Hot-swap the Ollama answer model at runtime.
    No-op if provider is Anthropic (Claude is always used then).
    Returns the new status dict.
    """
    global answer_llm
    provider = _resolve_provider()
    if provider == "anthropic":
        return {"swapped": False, "reason": "Provider is Claude — Ollama model ignored"}

    available = [m["name"] for m in list_ollama_models()]
    if model_name not in available:
        return {
            "swapped": False,
            "reason": f"Model '{model_name}' not found in Ollama. Available: {available}",
        }

    _state["answer_model"] = model_name
    answer_llm = _build_answer_llm(model_name)
    return {"swapped": True, "model": model_name}


# ─────────────────────────────────────────────────────────────────────────────
# Status helper
# ─────────────────────────────────────────────────────────────────────────────

def llm_status() -> dict:
    provider = _resolve_provider()
    available_ollama = list_ollama_models()
    return {
        "router": {
            "provider": "ollama",
            "model": OLLAMA_ROUTER_MODEL,
        },
        "answer": {
            "provider": provider,
            "model": ANTHROPIC_MODEL if provider == "anthropic" else _state["answer_model"],
        },
        "hybrid": provider == "anthropic",
        "available_ollama_models": available_ollama,
    }
