import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional



LANGUAGE_OPTIONS = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Russian": "ru",
}

CONNECTORS_BY_LANGUAGE = {
    "en": r"(and|but|or|so|because|then|that|which|when|as|if)",
    "fr": r"(et|mais|ou|donc|car|alors|que|qui|quand|comme|si)",
    "es": r"(y|pero|o|as[ií]|porque|entonces|que|quien|cuando|como|si)",
    "ru": r"(и|но|или|так|потому|тогда|что|который|когда|как|если)",
}


@dataclass
class SubtitleConfig:
    language: str = "en"
    split_gap: float = 0.5
    merge_gap: float = 0.15
    max_chars_per_line: int = 26
    padding: float = 1.0
    max_words_for_merge: int = 14
    model_size: str = "small"


def strip_trailing_comma(line: str) -> str:
    return re.sub(r",$", "", line.strip())


def _hash_key(audio_path: str, transcript_text: str, cfg: SubtitleConfig, mode: str) -> str:
    payload = {
        "audio_path": str(Path(audio_path).resolve()),
        "audio_mtime": os.path.getmtime(audio_path),
        "audio_size": os.path.getsize(audio_path),
        "transcript": transcript_text,
        "cfg": cfg.__dict__,
        "mode": mode,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_or_create_result(audio_path: str, transcript_text: Optional[str], cfg: SubtitleConfig, cache_dir: str):
    os.makedirs(cache_dir, exist_ok=True)
    mode = "align" if transcript_text and transcript_text.strip() else "transcribe"
    normalized_transcript = (transcript_text or "").strip()

    cache_key = _hash_key(audio_path, normalized_transcript, cfg, mode)
    cache_path = os.path.join(cache_dir, f"{cache_key}.json")

    if os.path.exists(cache_path):
        import stable_whisper
        return stable_whisper.WhisperResult(cache_path), cache_path, True

    import stable_whisper
    model = stable_whisper.load_model(cfg.model_size)
    if mode == "align":
        result = model.align(audio_path, normalized_transcript, language=cfg.language)
    else:
        result = model.transcribe(audio_path, language=cfg.language)

    result.save_as_json(cache_path)
    return result, cache_path, False


def extend_subtitle_ends_safely(result, padding: float, min_gap: float = 0.0):
    segments = result.segments
    for i, seg in enumerate(segments):
        desired_end = seg.end + padding
        if i == len(segments) - 1:
            seg.end = desired_end
            continue

        max_safe_end = segments[i + 1].start - min_gap
        seg.end = min(desired_end, max_safe_end)


def split_balanced_line(line: str, max_chars: int, language: str) -> str:
    line = line.strip()
    if len(line) <= max_chars:
        return line

    mid = int(len(line) * 0.55)
    words = line.split()
    connectors = CONNECTORS_BY_LANGUAGE.get(language, CONNECTORS_BY_LANGUAGE["en"])

    best = None
    left = ""
    for i in range(len(words) - 1):
        left = (left + " " + words[i]).strip()
        right = " ".join(words[i + 1 :])

        if len(left) > max_chars or len(right) > max_chars:
            continue

        score = 0
        if re.search(r"[,.;!?]$", left):
            score += 5
        if re.match(rf"^{connectors}\\b", right, re.I):
            score += 4
        score -= abs(len(left) - mid)

        if not best or score > best["score"]:
            best = {"score": score, "left": left, "right": right}

    if best:
        return best["left"] + "\n" + best["right"]

    m = re.match(rf"^(.{{1,{max_chars}}})\s+(.*)$", line)
    if m:
        return m.group(1) + "\n" + m.group(2)

    return line


def balance_srt(srt_path: str, max_chars_per_line: int, language: str):
    with open(srt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.isdigit() or "-->" in stripped or stripped == "":
            new_lines.append(line)
        else:
            stripped = strip_trailing_comma(stripped)
            balanced = split_balanced_line(stripped, max_chars_per_line, language)
            new_lines.append(balanced + "\n")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def generate_srt(audio_path: str, transcript_text: Optional[str], cfg: SubtitleConfig, cache_dir: str = "./cache"):
    result, cache_path, cache_hit = get_or_create_result(audio_path, transcript_text, cfg, cache_dir)

    (
        result.merge_all_segments()
        .split_by_punctuation([(".", " "), "!", "?", ":"])
        .split_by_gap(cfg.split_gap)
        .merge_by_gap(cfg.merge_gap, max_words=cfg.max_words_for_merge)
        .split_by_length(max_chars=cfg.max_chars_per_line * 2)
    )

    extend_subtitle_ends_safely(result, padding=cfg.padding, min_gap=0.0)

    temp_dir = tempfile.mkdtemp(prefix="stable_ts_wrap_")
    output_srt = os.path.join(temp_dir, "output.srt")
    result.to_srt_vtt(output_srt, segment_level=True, word_level=False)
    balance_srt(output_srt, max_chars_per_line=cfg.max_chars_per_line, language=cfg.language)

    return output_srt, cache_path, cache_hit
