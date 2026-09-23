import React from "react";
import {AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame} from "remotion";
import {Audio, Video} from "@remotion/media";
import {WordCaptions, Word} from "./WordCaptions";
import {DESIGN_TOKENS} from "./design-tokens";
import {EditorialPrimitive, VisualEvent} from "./EditorialVisuals";

type Fps = {num: number; den: number};
type Track = {id: string; kind: "audio" | "video" | "generated"; role: string; allowOverlap: boolean; zIndex: number};
type Clip = {id: string; trackId: string; role: string; kind: "audio" | "video" | "generated"; startFrame: number; durationFrames: number; zIndex: number; src?: string; sourceRangeUs?: [number, number]; sourceFrameRate?: Fps | null; playbackRate?: Fps; freezeFrameUs?: number | null; freezeSrc?: string; pitchPolicy?: "preserve" | "follow-rate" | "mute"; generator?: string; payload?: Record<string, unknown>};
type Caption = Word & {id: string; sourceWordId: string; clipId: string};
type Event = {id: string; frames: [number, number]; presentation: string; layers: Record<string, string[]>; sequence: string[]; purpose: string};
export type EditorialTimelineData = {schema: "render-timeline"; version: 2; fps: Fps; width: number; height: number; totalFrames: number; tracks: Track[]; clips: Clip[]; captions: Caption[]; visualEvents: Event[]};

const fpsNumber = (fps: Fps) => fps.num / fps.den;
const rate = (clip: Clip) => clip.playbackRate ? fpsNumber(clip.playbackRate) : 1;
const sourceFrame = (clip: Clip) => Math.round((clip.freezeFrameUs ?? clip.sourceRangeUs?.[0] ?? 0) * fpsNumber(clip.sourceFrameRate ?? {num: 30, den: 1}) / 1_000_000);
const canvas = (DESIGN_TOKENS as {colors?: {background?: string}}).colors?.background ?? "#101418";

const SourceVideo: React.FC<{clip: Clip}> = ({clip}) => clip.freezeFrameUs === null || clip.freezeFrameUs === undefined ? <Video src={staticFile(clip.src!)} trimBefore={sourceFrame(clip)} playbackRate={rate(clip)} muted name={`${clip.role}:${clip.id}`} style={{width: "100%", height: "100%", objectFit: "cover"}} /> : <Img src={staticFile(clip.freezeSrc!)} style={{width: "100%", height: "100%", objectFit: "cover"}} />;
const SourceAudio: React.FC<{clip: Clip}> = ({clip}) => clip.pitchPolicy === "mute" ? null : <Audio src={staticFile(clip.src!)} trimBefore={sourceFrame(clip)} playbackRate={rate(clip)} />;

export const EditorialTimeline: React.FC<{data: EditorialTimelineData; masterStart?: number; showSafeArea?: boolean}> = ({data, masterStart = 0, showSafeArea = false}) => {
  const frame = useCurrentFrame() + masterStart;
  const tracks = new Map(data.tracks.map(track => [track.id, track]));
  const safeArea = {top: .06, right: .06, bottom: .12, left: .06};
  const visual = data.clips.filter(clip => tracks.get(clip.trackId)?.kind !== "audio").sort((left, right) => left.zIndex - right.zIndex);
  const audio = data.clips.filter(clip => tracks.get(clip.trackId)?.kind === "audio");
  return <AbsoluteFill style={{background: canvas, overflow: "hidden"}}>
    {visual.map(clip => <Sequence key={clip.id} from={clip.startFrame - masterStart} durationInFrames={clip.durationFrames} layout="none"><AbsoluteFill>{clip.kind === "generated" ? <EditorialPrimitive generator={clip.generator!} payload={clip.payload ?? {}} /> : <SourceVideo clip={clip} />}</AbsoluteFill></Sequence>)}
    {data.visualEvents.map(event => <Sequence key={event.id} from={event.frames[0] - masterStart} durationInFrames={event.frames[1] - event.frames[0]} layout="none"><VisualEvent event={event} /></Sequence>)}
    {audio.map(clip => <Sequence key={clip.id} from={clip.startFrame - masterStart} durationInFrames={clip.durationFrames} layout="none"><SourceAudio clip={clip} /></Sequence>)}
    <WordCaptions words={data.captions} time={frame / fpsNumber(data.fps)} safeArea={safeArea} />
    {showSafeArea && <div style={{position: "absolute", pointerEvents: "none", border: "3px dashed #00a878", top: `${safeArea.top * 100}%`, right: `${safeArea.right * 100}%`, bottom: `${safeArea.bottom * 100}%`, left: `${safeArea.left * 100}%`}} />}
  </AbsoluteFill>;
};
