import gc
import json
import re
from pathlib import Path

import torch


def clear_gpu_memory() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def safe_float(x, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def normalize_question_number(q) -> str:
    if q is None:
        return ""
    text = str(q).strip()
    match = re.search(r"\d+", text)
    return match.group(0) if match else text


def has_enough_text(text: str, min_chars: int = 100) -> bool:
    if not text:
        return False
    cleaned = text.strip()
    alpha_count = sum(ch.isalpha() for ch in cleaned)
    return len(cleaned) >= min_chars and alpha_count >= 50


def extract_json_from_model_output(text: str) -> dict:
    if text is None:
        raise ValueError("Model output is None")

    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output:\n" + text[:1000])

    return json.loads(text[start:end + 1])


def write_json(path: str | Path, data: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_json(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))
