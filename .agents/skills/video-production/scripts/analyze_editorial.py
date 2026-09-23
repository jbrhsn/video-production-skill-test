#!/usr/bin/env python3
"""Produce deterministic editorial evidence from corrected source words.

This first analyzer intentionally produces candidates only. It never alters the
editorial timeline and labels each inference separately from measured timing.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _word(value, index):
    if not isinstance(value, dict) or set(value) - {"id", "word", "start", "end", "speaker"}:
        raise ValueError(f"word {index} contains unsupported fields")
    word_id = value.get("id")
    token = value.get("word")
    start, end = value.get("start"), value.get("end")
    if not isinstance(word_id, str) or not word_id or not isinstance(token, str) or not token.strip():
        raise ValueError(f"word {index} requires id and word")
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end <= start:
        raise ValueError(f"word {index} requires increasing start/end seconds")
    return {**value, "start": float(start), "end": float(end)}


def _normalized(value):
    return re.sub(r"[^a-z0-9']+", "", value.lower())


def analyze(data, silence_seconds=1.0, phrase_words=3):
    if not isinstance(data, dict) or set(data) != {"schema", "version", "words"} or data.get("schema") != "corrected-transcript" or data.get("version") != 1:
        raise ValueError("transcript requires schema corrected-transcript version 1")
    if not isinstance(data["words"], list):
        raise ValueError("transcript.words must be a list")
    words = [_word(value, index) for index, value in enumerate(data["words"])]
    if any(current["start"] < previous["end"] for previous, current in zip(words, words[1:])):
        raise ValueError("transcript words must not overlap")
    events, candidates = [], []
    for previous, current in zip(words, words[1:]):
        gap = current["start"] - previous["end"]
        if gap >= silence_seconds:
            events.append({"id": f"silence:{previous['id']}:{current['id']}", "type": "silence",
                           "rangeSeconds": [previous["end"], current["start"]], "durationSeconds": gap,
                           "confidence": 1.0, "evidence": {"beforeWordId": previous["id"], "afterWordId": current["id"]}})
    for word in words:
        if re.search(r"[.!?;:]$", word["word"]):
            events.append({"id": f"sentence:{word['id']}", "type": "sentence-boundary",
                           "rangeSeconds": [word["start"], word["end"]], "confidence": 1.0,
                           "evidence": {"wordId": word["id"]}})
    for index in range(len(words) - phrase_words + 1):
        phrase = tuple(_normalized(word["word"]) for word in words[index:index + phrase_words])
        if not all(phrase):
            continue
        for other in range(index + phrase_words, len(words) - phrase_words + 1):
            comparison = tuple(_normalized(word["word"]) for word in words[other:other + phrase_words])
            if phrase != comparison:
                continue
            candidate_id = f"repeat:{words[index]['id']}:{words[other]['id']}"
            candidates.append({"id": candidate_id, "type": "candidate-repeated-phrase", "confidence": 0.9,
                               "rangeSeconds": [words[other]["start"], words[other + phrase_words - 1]["end"]],
                               "relatedRangeSeconds": [words[index]["start"], words[index + phrase_words - 1]["end"]],
                               "reason": "Exact normalized phrase repeats later in the corrected transcript",
                               "requiresEditorialDecision": True,
                               "context": {"beforeWordId": words[max(0, other - 1)]["id"],
                                           "afterWordId": words[min(len(words) - 1, other + phrase_words)]["id"]}})
    return {"schema": "editorial-analysis", "version": 1, "coverage": {"words": len(words), "detectors": ["silence", "sentence-boundary", "exact-repetition"]},
            "events": events, "candidates": candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--silence-seconds", type=float, default=1.0)
    parser.add_argument("--phrase-words", type=int, default=3)
    args = parser.parse_args()
    if args.silence_seconds <= 0 or args.phrase_words < 2:
        parser.error("silence-seconds must be positive and phrase-words must be at least 2")
    transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    analysis = analyze(transcript, args.silence_seconds, args.phrase_words)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(f"Analyzed {analysis['coverage']['words']} words: {len(analysis['events'])} events, {len(analysis['candidates'])} candidates -> {output}")


if __name__ == "__main__":
    main()
