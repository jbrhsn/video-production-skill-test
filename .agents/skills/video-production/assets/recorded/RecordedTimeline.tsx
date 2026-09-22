import React from "react";
import {AbsoluteFill, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {Audio, Video} from "@remotion/media";
import {WordCaptions, Word} from "./WordCaptions";
import {DESIGN_TOKENS} from "./design-tokens";

type Rect = {x: number; y: number; w: number; h: number; radius: number; opacity: number};
type Track = {sourceId: string; src: string; sourceStartFrame: number; sourceEndFrame: number;
  playbackRate: number; width?: number; height?: number};
type LayoutEvent = {id: string; atFrame: number; durationFrames: number; layout: string; fromLayout?: string; corner: string};
type Mask = {id: string; startFrame: number; endFrame: number; rect: [number, number, number, number];
  strategy: "solid" | "blur"; color?: string};
type Annotation = {id: string; startFrame: number; endFrame: number; rect: [number, number, number, number];
  style?: "outline" | "highlight"};
type Clip = {id: string; scene: number; startFrame: number; durationFrames: number;
  tracks: {screen?: Track; presenter?: Track};
  audio: {sourceId: string; src: string; sourceStartFrame: number; playbackRate: number}; layouts: LayoutEvent[];
  masks: Mask[]; annotations: Annotation[]};
export type RecordedTimelineData = {version: 3; track: "recorded-edit"; fps: number; width: number; height: number;
  totalFrames: number; clips: Clip[]; scenes: {scene: number; id: string; startFrame: number; durationFrames: number}[];
  boundaries: {afterScene: number; frame: number; startFrame: number; durationFrames: number}[];
  words: Word[]; safeArea: {top: number; right: number; bottom: number; left: number}};

const TOKENS = DESIGN_TOKENS as {colors?: {background?: string; surface?: string; primary?: string}; shape?: {shadow?: string}};
const canvas = TOKENS.colors?.background ?? "#eef1f5";
const annotationColor = TOKENS.colors?.primary ?? "#ef4444";

const corners: Record<string, {x: number; y: number}> = {
  "top-left": {x: .035, y: .045}, "top-right": {x: .745, y: .045},
  "bottom-left": {x: .035, y: .65}, "bottom-right": {x: .745, y: .65},
};
const rects = (layout: string, corner: string): {screen: Rect; presenter: Rect} => {
  const small = corners[corner] ?? corners["top-right"];
  const primary = {x: .035, y: .04, w: .93, h: .88, radius: 22, opacity: 1};
  const pip = {x: small.x, y: small.y, w: .22, h: .27, radius: 20, opacity: 1};
  if (layout === "presenter-focus") return {presenter: primary, screen: {...pip, w: .25}};
  if (layout === "balanced") return {
    screen: {x: .035, y: .08, w: .62, h: .78, radius: 18, opacity: 1},
    presenter: {x: .68, y: .08, w: .285, h: .78, radius: 18, opacity: 1},
  };
  if (layout === "presenter-only") return {presenter: primary, screen: {...pip, opacity: 0}};
  if (layout === "screen-only") return {screen: primary, presenter: {...pip, opacity: 0}};
  return {screen: primary, presenter: pip};
};
const mix = (a: Rect, b: Rect, p: number): Rect => ({
  x: a.x + (b.x - a.x) * p, y: a.y + (b.y - a.y) * p,
  w: a.w + (b.w - a.w) * p, h: a.h + (b.h - a.h) * p,
  radius: a.radius + (b.radius - a.radius) * p, opacity: a.opacity + (b.opacity - a.opacity) * p,
});
const geometry = (events: LayoutEvent[], frame: number) => {
  let priorLayout = events[0].fromLayout ?? events[0].layout;
  let priorCorner = events[0].corner;
  for (const event of events) {
    if (frame < event.atFrame) return rects(priorLayout, priorCorner);
    const from = rects(event.fromLayout ?? priorLayout, priorCorner);
    const to = rects(event.layout, event.corner);
    const p = event.durationFrames <= 0 ? 1 : interpolate(frame, [event.atFrame, event.atFrame + event.durationFrames],
      [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
    if (p < 1) return {screen: mix(from.screen, to.screen, p), presenter: mix(from.presenter, to.presenter, p)};
    priorLayout = event.layout;
    priorCorner = event.corner;
  }
  return rects(priorLayout, priorCorner);
};

const Layer: React.FC<{role: "screen" | "presenter"; track?: Track; rect: Rect; masks: Mask[];
  annotations: Annotation[]; frame: number}> = ({role, track, rect, masks, annotations, frame}) => {
  const {width, height} = useVideoConfig();
  if (!track || rect.opacity <= 0) return null;
  const boxW = rect.w * width, boxH = rect.h * height;
  const sourceRatio = (track.width ?? boxW) / (track.height ?? boxH);
  const boxRatio = boxW / boxH;
  const mediaW = sourceRatio > boxRatio ? boxW : boxH * sourceRatio;
  const mediaH = sourceRatio > boxRatio ? boxW / sourceRatio : boxH;
  const mediaX = (boxW - mediaW) / 2, mediaY = (boxH - mediaH) / 2;
  return <div style={{position: "absolute", left: rect.x * width, top: rect.y * height, width: boxW, height: boxH,
    opacity: rect.opacity, overflow: "hidden", borderRadius: rect.radius, background: TOKENS.colors?.surface ?? "#0b0d12",
    boxShadow: TOKENS.shape?.shadow ?? "0 12px 38px rgba(0,0,0,.25)"}}>
    <Video src={staticFile(track.src)} trimBefore={track.sourceStartFrame} playbackRate={track.playbackRate}
      muted name={`${role}:${track.sourceId}`}
      style={{position: "absolute", left: mediaX, top: mediaY, width: mediaW, height: mediaH, objectFit: "fill"}} />
    {role === "screen" && masks.filter(mask => frame >= mask.startFrame && frame < mask.endFrame).map(mask => {
      const [x, y, w, h] = mask.rect;
      return <div key={mask.id} style={{position: "absolute", left: mediaX + x * mediaW, top: mediaY + y * mediaH,
        width: w * mediaW, height: h * mediaH, background: mask.strategy === "solid" ? (mask.color ?? "#111") : "rgba(20,20,20,.35)",
        backdropFilter: mask.strategy === "blur" ? "blur(18px)" : undefined}} />;
    })}
    {role === "screen" && annotations.filter(item => frame >= item.startFrame && frame < item.endFrame).map(item => {
      const [x, y, w, h] = item.rect;
      return <div key={item.id} style={{position: "absolute", left: mediaX + x * mediaW, top: mediaY + y * mediaH,
        width: w * mediaW, height: h * mediaH, boxSizing: "border-box", pointerEvents: "none",
        border: `3px solid ${annotationColor}`, borderRadius: 8,
        background: item.style === "highlight" ? "rgba(239,68,68,.12)" : "transparent"}} />;
    })}
  </div>;
};

const RecordedClip: React.FC<{clip: Clip}> = ({clip}) => {
  const local = useCurrentFrame();
  const stage = geometry(clip.layouts, local);
  return <AbsoluteFill style={{background: canvas}}>
    <Layer role="screen" track={clip.tracks.screen} rect={stage.screen} masks={clip.masks}
      annotations={clip.annotations ?? []} frame={local} />
    <Layer role="presenter" track={clip.tracks.presenter} rect={stage.presenter} masks={[]}
      annotations={[]} frame={local} />
    <Audio src={staticFile(clip.audio.src)} trimBefore={clip.audio.sourceStartFrame} playbackRate={clip.audio.playbackRate} />
  </AbsoluteFill>;
};

export const RecordedTimeline: React.FC<{data: RecordedTimelineData; masterStart?: number; showSafeArea?: boolean}> =
({data, masterStart = 0, showSafeArea = false}) => {
  const local = useCurrentFrame();
  const master = local + masterStart;
  return <AbsoluteFill style={{background: canvas, overflow: "hidden"}}>
    {data.clips.map(clip => <Sequence key={clip.id} from={clip.startFrame - masterStart} durationInFrames={clip.durationFrames}>
      <RecordedClip clip={clip} />
    </Sequence>)}
    <WordCaptions words={data.words} time={master / data.fps} safeArea={data.safeArea} />
    {showSafeArea && <div style={{position: "absolute", pointerEvents: "none", border: "3px dashed #00a878",
      top: `${data.safeArea.top * 100}%`, right: `${data.safeArea.right * 100}%`,
      bottom: `${data.safeArea.bottom * 100}%`, left: `${data.safeArea.left * 100}%`}} />}
  </AbsoluteFill>;
};
