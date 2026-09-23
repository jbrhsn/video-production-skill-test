#!/usr/bin/env python3
"""Create evidence and non-destructive editorial candidates from a transcript."""
from __future__ import annotations

import argparse, json, re
from pathlib import Path


def _word(value, index):
    allowed = {"id", "word", "start", "end", "speaker", "confidence", "sourceScene", "uiEvent"}
    if not isinstance(value, dict) or set(value) - allowed: raise ValueError(f"word {index} contains unsupported fields")
    if not isinstance(value.get("id"), str) or not value["id"] or not isinstance(value.get("word"), str) or not value["word"].strip(): raise ValueError(f"word {index} requires id and word")
    if not isinstance(value.get("start"), (int, float)) or not isinstance(value.get("end"), (int, float)) or value["start"] < 0 or value["end"] <= value["start"]: raise ValueError(f"word {index} requires increasing start/end")
    return {**value, "start": float(value["start"]), "end": float(value["end"]), "confidence": float(value.get("confidence", 1.0))}


def _norm(value): return re.sub(r"[^a-z0-9']+", "", value.lower())
def _candidate(kind, words, reason, confidence=.7, **extra):
    return {"id": f"{kind}:{words[0]['id']}:{words[-1]['id']}", "type": f"candidate-{kind}", "rangeSeconds": [words[0]["start"], words[-1]["end"]], "confidence": confidence, "reason": reason, "requiresEditorialDecision": True, **extra}


def analyze(data, silence_seconds=1.0, phrase_words=3):
    if not isinstance(data, dict) or data.get("schema") != "corrected-transcript" or data.get("version") != 2 or set(data) - {"schema", "version", "words", "detectors", "gaps"}:
        raise ValueError("transcript requires corrected-transcript version 2")
    words = [_word(value, index) for index, value in enumerate(data.get("words", []))]
    if any(current["start"] < previous["end"] for previous, current in zip(words, words[1:])): raise ValueError("transcript words must not overlap")
    events, candidates, unavailable = [], [], []
    declared = data.get("detectors", {"speaker": "unavailable", "scene": "unavailable", "ui": "unavailable"})
    for name, state in declared.items():
        if state == "unavailable": unavailable.append({"detector": name, "status": "unavailable", "coverage": 0})
    for previous, current in zip(words, words[1:]):
        gap = current["start"] - previous["end"]
        if gap >= silence_seconds:
            pause = "dramatic" if gap >= 2.0 or re.search(r"[.!?]$", previous["word"]) else "edit-candidate"
            events.append({"id": f"silence:{previous['id']}:{current['id']}", "type": "silence", "classification": pause, "rangeSeconds": [previous["end"], current["start"]], "durationSeconds": gap, "confidence": 1.0, "evidence": {"beforeWordId": previous["id"], "afterWordId": current["id"]}})
        if previous.get("speaker") and current.get("speaker") and previous["speaker"] != current["speaker"]:
            events.append({"id": f"speaker:{previous['id']}:{current['id']}", "type": "speaker-change", "rangeSeconds": [previous["end"], current["start"]], "confidence": min(previous["confidence"], current["confidence"]), "evidence": {"from": previous["speaker"], "to": current["speaker"]}})
        if previous.get("sourceScene") and current.get("sourceScene") and previous["sourceScene"] != current["sourceScene"]:
            events.append({"id": f"scene:{previous['id']}:{current['id']}", "type": "source-scene-change", "rangeSeconds": [previous["end"], current["start"]], "confidence": .8, "evidence": {"from": previous["sourceScene"], "to": current["sourceScene"]}})
    for word in words:
        if re.search(r"[.!?;:]$", word["word"]): events.append({"id": f"sentence:{word['id']}", "type": "sentence-boundary", "rangeSeconds": [word["start"], word["end"]], "confidence": word["confidence"], "evidence": {"wordId": word["id"]}})
        if word.get("uiEvent"): events.append({"id": f"ui:{word['id']}", "type": "ui-event", "rangeSeconds": [word["start"], word["end"]], "confidence": word["confidence"], "evidence": {"event": word["uiEvent"]}})
    for index in range(len(words) - phrase_words + 1):
        phrase = tuple(_norm(word["word"]) for word in words[index:index + phrase_words])
        if not all(phrase): continue
        for other in range(index + phrase_words, len(words) - phrase_words + 1):
            if phrase == tuple(_norm(word["word"]) for word in words[other:other + phrase_words]):
                candidates.append(_candidate("repeated-phrase", words[other:other + phrase_words], "Exact normalized phrase repeats later", .9, relatedRangeSeconds=[words[index]["start"], words[index + phrase_words - 1]["end"]]))
    for index, word in enumerate(words):
        if _norm(word["word"]) in {"sorry", "actually", "rather", "instead"} and index + 1 < len(words): candidates.append(_candidate("retake", words[max(0, index - 2):index + 2], "Self-correction marker requires editorial review", .55))
        if _norm(word["word"]) in {"this", "that", "they", "it"}: candidates.append(_candidate("context-dependent-extract", [word], "Pronoun may lose its antecedent in an isolated clip", .5))
    return {"schema": "editorial-analysis", "version": 2, "coverage": {"words": len(words), "timeDomain": "source-seconds", "detectors": ["silence", "sentence-boundary", "exact-repetition", "self-correction", "speaker-change", "source-scene-change", "ui-event"], "gaps": data.get("gaps", [])}, "unavailableDetectors": unavailable, "events": events, "candidates": candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--transcript", required=True); parser.add_argument("--out", required=True); parser.add_argument("--silence-seconds", type=float, default=1.0); parser.add_argument("--phrase-words", type=int, default=3); args = parser.parse_args()
    if args.silence_seconds <= 0 or args.phrase_words < 2: parser.error("silence-seconds must be positive and phrase-words at least 2")
    report = analyze(json.loads(Path(args.transcript).read_text()), args.silence_seconds, args.phrase_words); out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__": main()
