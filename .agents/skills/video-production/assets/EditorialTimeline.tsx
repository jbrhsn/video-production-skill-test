import React from "react";
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame} from "remotion";
import {Audio, Video} from "@remotion/media";
import {WordCaptions, Word} from "./WordCaptions";
import {DESIGN_TOKENS} from "./design-tokens";

type Fps = {num: number; den: number};
type Track = {id: string; kind: "audio" | "video" | "generated"; role: string; allowOverlap: boolean};
type Clip = {id: string; trackId: string; role: string; sourceId: string; streamId: string; src: string;
  sourceRangeUs: [number, number]; startFrame: number; durationFrames: number; playbackRate: Fps};
type Caption = Word & {id: string; sourceWordId: string; clipId: string};
export type EditorialTimelineData = {schema: "render-timeline"; version: 1; fps: Fps; width: number; height: number;
  totalFrames: number; tracks: Track[]; clips: Clip[]; captions: Caption[]};

const fpsNumber = (fps: Fps) => fps.num / fps.den;
const clipRate = (clip: Clip) => clip.playbackRate.num / clip.playbackRate.den;
const sourceFrame = (clip: Clip, fps: Fps) => Math.round(clip.sourceRangeUs[0] * fpsNumber(fps) / 1_000_000);
const canvas = (DESIGN_TOKENS as {colors?: {background?: string}}).colors?.background ?? "#101418";

const VideoClip: React.FC<{clip: Clip; fps: Fps}> = ({clip, fps}) =>
  <Video src={staticFile(clip.src)} trimBefore={sourceFrame(clip, fps)} playbackRate={clipRate(clip)} muted
    name={`${clip.role}:${clip.id}`} style={{width: "100%", height: "100%", objectFit: "cover"}} />;

const AudioClip: React.FC<{clip: Clip; fps: Fps}> = ({clip, fps}) =>
  <Audio src={staticFile(clip.src)} trimBefore={sourceFrame(clip, fps)} playbackRate={clipRate(clip)} />;

export const EditorialTimeline: React.FC<{data: EditorialTimelineData; masterStart?: number; showSafeArea?: boolean}> =
({data, masterStart = 0, showSafeArea = false}) => {
  const frame = useCurrentFrame() + masterStart;
  const videoTracks = new Map(data.tracks.filter(track => track.kind === "video").map(track => [track.id, track]));
  const audioTracks = new Map(data.tracks.filter(track => track.kind === "audio").map(track => [track.id, track]));
  const safeArea = {top: .06, right: .06, bottom: .12, left: .06};
  return <AbsoluteFill style={{background: canvas, overflow: "hidden"}}>
    {data.clips.filter(clip => videoTracks.has(clip.trackId)).map(clip => <Sequence key={clip.id}
      from={clip.startFrame - masterStart} durationInFrames={clip.durationFrames} layout="none">
      <AbsoluteFill><VideoClip clip={clip} fps={data.fps} /></AbsoluteFill>
    </Sequence>)}
    {data.clips.filter(clip => audioTracks.has(clip.trackId)).map(clip => <Sequence key={clip.id}
      from={clip.startFrame - masterStart} durationInFrames={clip.durationFrames} layout="none">
      <AudioClip clip={clip} fps={data.fps} />
    </Sequence>)}
    <WordCaptions words={data.captions} time={frame / fpsNumber(data.fps)} safeArea={safeArea} />
    {showSafeArea && <div style={{position: "absolute", pointerEvents: "none", border: "3px dashed #00a878",
      top: `${safeArea.top * 100}%`, right: `${safeArea.right * 100}%`, bottom: `${safeArea.bottom * 100}%`, left: `${safeArea.left * 100}%`}} />}
  </AbsoluteFill>;
};
