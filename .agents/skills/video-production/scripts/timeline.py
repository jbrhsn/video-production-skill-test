"""Compile a versioned edit plan without altering measured narration durations."""
from __future__ import annotations

import math
from pathlib import PurePosixPath


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def keys(value, allowed, label):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError(f"{label} must be an object with only: {', '.join(allowed)}")


def gain(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be finite and between 0 and 1")
    return value


def number(value, label, minimum=None, maximum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return value


def db_gain(value, label):
    value = number(value, label, -96, 6)
    return 10 ** (value / 20)


def _resolve_anchor(anchor, tracks, boundaries, total, events, word_frames):
    if not isinstance(anchor, dict) or not isinstance(anchor.get("type"), str):
        raise ValueError("audio anchor must be an object with a type")
    kind = anchor["type"]
    offset = integer(anchor.get("offsetFrames", 0), "audio.anchor.offsetFrames") if anchor.get("offsetFrames", 0) >= 0 else anchor.get("offsetFrames")
    if type(offset) is not int:
        raise ValueError("audio.anchor.offsetFrames must be an integer")
    by_scene = {track["scene"]: track for track in tracks}
    if kind == "master-start":
        frame = 0
    elif kind == "master-end":
        frame = total
    elif kind in ("scene-start", "scene-end", "scene-span-end"):
        scene = integer(anchor.get("scene"), "audio.anchor.scene", 1)
        if scene not in by_scene:
            raise ValueError("audio anchor references an unknown scene")
        track = by_scene[scene]
        frame = track["start"] if kind == "scene-start" else track["start"] + (
            track["contentFrames"] if kind == "scene-end" else track["spanFrames"])
    elif kind == "transition":
        after = integer(anchor.get("afterScene"), "audio.anchor.afterScene", 1)
        match = next((item for item in boundaries if item["afterScene"] == after), None)
        if match is None:
            raise ValueError("transition anchor references an unknown boundary")
        frame = match["frame"]
    elif kind == "event":
        key = (anchor.get("scene"), anchor.get("beat"), anchor.get("event"))
        if key not in events:
            raise ValueError(f"audio anchor references an unknown execution event: {key}")
        frame = events[key]
    elif kind == "word":
        key = (anchor.get("scene"), anchor.get("index"), anchor.get("edge", "start"))
        if key not in word_frames:
            raise ValueError(f"audio anchor references an unknown checked word boundary: {key}")
        frame = word_frames[key]
    elif kind == "absolute":
        frame = integer(anchor.get("frame"), "audio.anchor.frame")
        if not isinstance(anchor.get("reason"), str) or not anchor["reason"].strip():
            raise ValueError("absolute audio anchors require a reason")
    else:
        raise ValueError(f"unsupported audio anchor type: {kind}")
    resolved = frame + offset
    if resolved < 0:
        raise ValueError("audio anchor plus offset resolves before the timeline")
    return resolved


def _events(execution, tracks):
    if execution is None:
        return {}
    starts = {track["scene"]: track["start"] for track in tracks}
    result = {}
    for scene in execution.get("scenes", []):
        for beat in scene.get("beats", []):
            for event in beat.get("events", []):
                key = (scene["scene"], beat["id"], event["id"])
                if key in result:
                    raise ValueError(f"duplicate execution event: {key}")
                result[key] = starts[scene["scene"]] + event["frame"]
    return result


def compile_timeline(scenes, fps, plan=None, execution=None, assets=None, word_frames=None):
    plan = {"version": 1} if plan is None else plan
    version = plan.get("version")
    allowed = ("version", "transitions", "holds", "audio", "safeArea", "mix") if version == 2 else (
        "version", "transitions", "holds", "audio", "safeArea")
    keys(plan, allowed, "edit plan")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("edit plan version must be 1 or 2")
    for field in ("transitions", "holds", "audio"):
        if not isinstance(plan.get(field, []), list):
            raise ValueError(f"{field} must be an array")
    holds = {}
    for hold in plan.get("holds", []):
        keys(hold, ("afterScene", "frames"), "hold")
        scene = integer(hold.get("afterScene"), "hold.afterScene", 1)
        if scene > len(scenes) or scene in holds:
            raise ValueError("holds must reference distinct existing scenes")
        holds[scene] = integer(hold.get("frames"), "hold.frames")
    tracks, cursor = [], 0
    for scene in scenes:
        content = scene["duration_frames"]
        span = content + holds.get(scene["scene"], 0)
        tracks.append(dict(scene=scene["scene"], start=cursor, contentFrames=content,
                           spanFrames=span, visualStart=cursor, visualEnd=cursor + span))
        cursor += span
    boundaries = [dict(afterScene=i + 1, frame=tracks[i + 1]["start"], kind="cut",
                       frames=0, direction="left", easing="smooth") for i in range(len(tracks) - 1)]
    seen = set()
    for transition in plan.get("transitions", []):
        keys(transition, ("afterScene", "kind", "frames", "direction", "easing"), "transition")
        scene = integer(transition.get("afterScene"), "transition.afterScene", 1)
        if scene >= len(scenes) or scene in seen:
            raise ValueError("transitions must reference distinct interior boundaries")
        seen.add(scene)
        kind = transition.get("kind", "cut")
        if kind not in ("cut", "fade", "slide", "wipe"):
            raise ValueError("transition kind must be cut, fade, slide, or wipe")
        duration = integer(transition.get("frames", 0), "transition.frames")
        if (kind == "cut" and duration != 0) or (kind != "cut" and duration < 2):
            raise ValueError("cuts need zero frames; animated transitions need at least two")
        direction = transition.get("direction", "left")
        easing = transition.get("easing", "smooth")
        if direction not in ("left", "right", "up", "down") or easing not in ("linear", "smooth"):
            raise ValueError("invalid transition direction or easing")
        boundaries[scene - 1].update(kind=kind, frames=duration, direction=direction, easing=easing)
    for i, track in enumerate(tracks):
        incoming = boundaries[i - 1]["frames"] if i else 0
        outgoing = boundaries[i]["frames"] if i < len(boundaries) else 0
        # Reserve at least one stable frame between transitions inside this scene.
        if (incoming - incoming // 2) + outgoing // 2 >= track["spanFrames"] and (incoming or outgoing):
            raise ValueError(f"Scene {i + 1}: transition windows consume the scene; shorten transitions")
        track["visualStart"] -= incoming // 2
        track["visualEnd"] += outgoing - outgoing // 2
    for boundary in boundaries:
        before = boundary["frames"] // 2
        boundary["previewStart"] = max(0, boundary["frame"] - before - fps)
        end = min(cursor, boundary["frame"] + boundary["frames"] - before + fps)
        boundary["previewFrames"] = end - boundary["previewStart"]
    for track in tracks:
        track["reviewStart"] = max(0, track["visualStart"])
        track["reviewFrames"] = min(cursor, track["visualEnd"]) - track["reviewStart"]
    audio = []
    events = _events(execution, tracks)
    word_frames = word_frames or {}
    asset_map = {item["id"]: item for item in (assets or {}).get("assets", [])}
    cue_ids = set()
    for cue in plan.get("audio", []):
        if version == 1:
            keys(cue, ("src", "role", "startFrame", "durationFrames", "volume", "fadeFrames", "duckVolume"), "audio cue")
            src = cue.get("src")
            role = cue.get("role")
            start = integer(cue.get("startFrame"), "audio.startFrame")
            duration = integer(cue.get("durationFrames"), "audio.durationFrames", 1)
            fade_in = fade_out = integer(cue.get("fadeFrames", min(round(fps * .1), duration // 2)), "audio.fadeFrames")
            volume = gain(cue.get("volume", .15 if role == "music" else .35), "audio.volume")
            duck = gain(cue.get("duckVolume", volume * .4 if role == "music" else volume), "audio.duckVolume")
            trim_before = 0
            attack = release = max(1, round(fps * .15))
            cue_id = f"legacy-{len(audio) + 1}"
            purpose = "legacy cue"
        else:
            keys(cue, ("id", "assetId", "role", "purpose", "required", "anchor", "durationFrames",
                       "sourceStartSeconds", "gainDb", "duckGainDb", "duckAttackFrames",
                       "duckReleaseFrames", "fadeInFrames", "fadeOutFrames", "acceptance"), "audio cue")
            cue_id = cue.get("id")
            if not isinstance(cue_id, str) or not cue_id.strip() or cue_id in cue_ids:
                raise ValueError("v2 audio cues require unique nonempty IDs")
            cue_ids.add(cue_id)
            asset_id = cue.get("assetId")
            if asset_id not in asset_map:
                raise ValueError(f"audio cue {cue_id} references unknown asset {asset_id!r}")
            item = asset_map[asset_id]
            src = item.get("stagedPath", "")
            if src.startswith("public/"):
                src = src[len("public/"):]
            role = cue.get("role")
            start = _resolve_anchor(cue.get("anchor"), tracks, boundaries, cursor, events, word_frames)
            duration = integer(cue.get("durationFrames"), f"audio {cue_id}.durationFrames", 1)
            fade_in = integer(cue.get("fadeInFrames", 0), f"audio {cue_id}.fadeInFrames")
            fade_out = integer(cue.get("fadeOutFrames", 0), f"audio {cue_id}.fadeOutFrames")
            trim_before = round(number(cue.get("sourceStartSeconds", 0), f"audio {cue_id}.sourceStartSeconds", 0) * fps)
            volume = db_gain(cue.get("gainDb", -16 if role in ("music", "ambience") else -9), f"audio {cue_id}.gainDb")
            duck = db_gain(cue.get("duckGainDb", cue.get("gainDb", -16)), f"audio {cue_id}.duckGainDb")
            attack = integer(cue.get("duckAttackFrames", max(1, round(fps * .15))), f"audio {cue_id}.duckAttackFrames", 1)
            release = integer(cue.get("duckReleaseFrames", max(1, round(fps * .15))), f"audio {cue_id}.duckReleaseFrames", 1)
            purpose = cue.get("purpose")
            if not isinstance(purpose, str) or not purpose.strip() or not isinstance(cue.get("acceptance"), str) or not cue["acceptance"].strip():
                raise ValueError(f"audio cue {cue_id} requires purpose and listening acceptance")
        if (not isinstance(src, str) or not src.startswith("media/") or "\\" in src
                or ":" in src or any(p in ("..", ".") for p in src.split("/"))
                or PurePosixPath(src).is_absolute()):
            raise ValueError("audio src must be a public-relative media/ path without traversal")
        if role not in (("music", "effect") if version == 1 else ("music", "effect", "ambience")):
            raise ValueError("invalid audio role")
        if start + duration > cursor or fade_in + fade_out > duration:
            raise ValueError(f"audio cue {cue_id} exceeds timeline or fades consume cue")
        if duck > volume:
            raise ValueError("duckVolume cannot exceed volume")
        audio.append(dict(id=cue_id, src=src, role=role, purpose=purpose, startFrame=start,
                          durationFrames=duration, trimBefore=trim_before, fadeInFrames=fade_in,
                          fadeOutFrames=fade_out, volume=volume, duckVolume=duck,
                          duckAttackFrames=attack, duckReleaseFrames=release))
    safe = plan.get("safeArea", {"top": .08, "right": .12, "bottom": .18, "left": .08})
    keys(safe, ("top", "right", "bottom", "left"), "safeArea")
    if set(safe) != {"top", "right", "bottom", "left"}:
        raise ValueError("safeArea requires top, right, bottom, left fractions")
    for name, value in safe.items():
        gain(value, f"safeArea.{name}")
    if safe["top"] + safe["bottom"] >= 1 or safe["left"] + safe["right"] >= 1:
        raise ValueError("safeArea must leave a visible content region")
    mix = plan.get("mix") if version == 2 else None
    if version == 2:
        keys(mix, ("targetLufs", "toleranceLufs", "maxTruePeakDbtp"), "mix")
        number(mix.get("targetLufs"), "mix.targetLufs", -36, -5)
        number(mix.get("toleranceLufs"), "mix.toleranceLufs", 0, 6)
        number(mix.get("maxTruePeakDbtp"), "mix.maxTruePeakDbtp", -9, 0)
    return dict(version=version, totalFrames=cursor, scenes=tracks, boundaries=boundaries,
                audio=audio, safeArea=safe, mix=mix)
