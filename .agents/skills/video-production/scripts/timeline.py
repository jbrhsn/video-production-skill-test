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


def compile_timeline(scenes, fps, plan=None):
    plan = {"version": 1} if plan is None else plan
    keys(plan, ("version", "transitions", "holds", "audio", "safeArea"), "edit plan")
    if type(plan.get("version")) is not int or plan["version"] != 1:
        raise ValueError("edit plan version must be 1")
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
    audio = []
    for cue in plan.get("audio", []):
        keys(cue, ("src", "role", "startFrame", "durationFrames", "volume", "fadeFrames", "duckVolume"), "audio cue")
        src = cue.get("src")
        if (not isinstance(src, str) or not src.startswith("media/") or "\\" in src
                or ":" in src or any(p in ("..", ".") for p in src.split("/"))
                or PurePosixPath(src).is_absolute()):
            raise ValueError("audio src must be a public-relative media/ path without traversal")
        role = cue.get("role")
        if role not in ("music", "effect"):
            raise ValueError("audio role must be music or effect")
        start = integer(cue.get("startFrame"), "audio.startFrame")
        duration = integer(cue.get("durationFrames"), "audio.durationFrames", 1)
        fade = integer(cue.get("fadeFrames", min(round(fps * .1), duration // 2)), "audio.fadeFrames")
        if start + duration > cursor or fade * 2 > duration:
            raise ValueError("audio cue exceeds timeline or fade consumes cue")
        volume = gain(cue.get("volume", .15 if role == "music" else .35), "audio.volume")
        duck = gain(cue.get("duckVolume", volume * .4 if role == "music" else volume), "audio.duckVolume")
        if duck > volume:
            raise ValueError("duckVolume cannot exceed volume")
        audio.append(dict(src=src, role=role, startFrame=start, durationFrames=duration,
                          fadeFrames=fade, volume=volume, duckVolume=duck))
    safe = plan.get("safeArea", {"top": .08, "right": .12, "bottom": .18, "left": .08})
    keys(safe, ("top", "right", "bottom", "left"), "safeArea")
    if set(safe) != {"top", "right", "bottom", "left"}:
        raise ValueError("safeArea requires top, right, bottom, left fractions")
    for name, value in safe.items():
        gain(value, f"safeArea.{name}")
    if safe["top"] + safe["bottom"] >= 1 or safe["left"] + safe["right"] >= 1:
        raise ValueError("safeArea must leave a visible content region")
    return dict(version=1, totalFrames=cursor, scenes=tracks, boundaries=boundaries,
                audio=audio, safeArea=safe)
