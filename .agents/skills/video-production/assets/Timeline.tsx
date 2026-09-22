import React from "react";
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {Audio} from "@remotion/media";
import {WordCaptions, Word} from "./WordCaptions";
import {DESIGN_TOKENS} from "./design-tokens";

export type VisualSceneProps = {contentFrame: number; rawContentFrame: number;
  durationFrames: number; fps: number; width: number; height: number};
type Track = {scene: number; start: number; contentFrames: number; spanFrames: number;
  visualStart: number; visualEnd: number; reviewStart: number; reviewFrames: number};
type Boundary = {afterScene: number; frame: number; kind: string; frames: number;
  direction: string; easing: string; previewStart: number; previewFrames: number};
type Cue = {id: string; src: string; role: string; startFrame: number; durationFrames: number;
  trimBefore: number; volume: number; duckVolume: number; fadeInFrames: number;
  fadeOutFrames: number; duckAttackFrames: number; duckReleaseFrames: number};
export type TimelineData = {totalFrames: number; scenes: Track[]; boundaries: Boundary[];
  audio: Cue[]; safeArea: {top: number; right: number; bottom: number; left: number}};
export type SceneEntry = {Visual: React.ComponentType<VisualSceneProps>; audioFile: string; words: Word[]};
const clamp = (n: number) => Math.max(0, Math.min(1, n));
const progress = (b: Boundary, frame: number) => {
  const p = clamp((frame - (b.frame - Math.floor(b.frames / 2))) / Math.max(1, b.frames - 1));
  return b.easing === "linear" ? p : p * p * (3 - 2 * p);
};
const translate = (direction: string, amount: number) =>
  direction === "up" || direction === "down"
    ? `translateY(${amount * (direction === "up" ? -100 : 100)}%)`
    : `translateX(${amount * (direction === "left" ? -100 : 100)}%)`;

const Visual: React.FC<{entry: SceneEntry; track: Track; incoming?: Boundary; outgoing?: Boundary}> =
({entry, track, incoming, outgoing}) => {
  const local = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const global = local + track.visualStart;
  const rawContentFrame = global - track.start;
  const style: React.CSSProperties = {overflow: "hidden"};
  if (incoming && incoming.frames && global < incoming.frame + Math.ceil(incoming.frames / 2)) {
    const p = progress(incoming, global);
    if (incoming.kind === "fade") style.opacity = p;
    if (incoming.kind === "slide") style.transform = translate(incoming.direction, p - 1);
    if (incoming.kind === "wipe") {
      const hidden = (1 - p) * 100;
      style.clipPath = incoming.direction === "left" ? `inset(0 0 0 ${hidden}%)`
        : incoming.direction === "right" ? `inset(0 ${hidden}% 0 0)`
        : incoming.direction === "up" ? `inset(${hidden}% 0 0 0)` : `inset(0 0 ${hidden}% 0)`;
    }
  }
  if (outgoing?.kind === "slide" && global >= outgoing.frame - Math.floor(outgoing.frames / 2)) {
    style.transform = translate(outgoing.direction, progress(outgoing, global));
  }
  const Component = entry.Visual;
  return <AbsoluteFill style={style}><Component rawContentFrame={rawContentFrame}
    contentFrame={Math.max(0, Math.min(track.contentFrames - 1, rawContentFrame))}
    durationFrames={track.contentFrames} fps={fps} width={width} height={height} /></AbsoluteFill>;
};

const Speech: React.FC<{entry: SceneEntry; safeArea: TimelineData["safeArea"]}> = ({entry, safeArea}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <><Audio src={staticFile(entry.audioFile)} />
    <WordCaptions words={entry.words} time={frame / fps} safeArea={safeArea} /></>;
};

// The cue envelope uses audio-local frame values; speech spans use master frames.
// Duck around narration segments, including their internal pauses, not word by word.
const CueAudio: React.FC<{cue: Cue; tracks: Track[]}> = ({cue, tracks}) => {
  const {fps} = useVideoConfig();
  const attack = cue.duckAttackFrames || Math.max(1, Math.round(fps * .15));
  const release = cue.duckReleaseFrames || attack;
  return <Audio src={staticFile(cue.src)} volume={(local) => {
    const global = cue.startFrame + local;
    const speech = cue.role === "music" ? Math.max(0, ...tracks.map(t =>
      Math.min(clamp((global - t.start + attack) / attack),
        clamp((t.start + t.contentFrames + release - global) / release)))) : 0;
    const edge = Math.min(cue.fadeInFrames ? clamp(local / cue.fadeInFrames) : 1,
      cue.fadeOutFrames ? clamp((cue.durationFrames - 1 - local) / cue.fadeOutFrames) : 1);
    return edge * (cue.volume + (cue.duckVolume - cue.volume) * speech);
  }} trimBefore={cue.trimBefore || 0} />;
};

export const Timeline: React.FC<{data: TimelineData; entries: SceneEntry[]; showSafeArea?: boolean}> =
({data, entries, showSafeArea = false}) => <AbsoluteFill style={{background: DESIGN_TOKENS.colors.background, overflow: "hidden"}}>
  {data.scenes.map((track, i) => <Sequence key={`visual-${i}`} from={track.visualStart}
    durationInFrames={track.visualEnd - track.visualStart}>
    <Visual entry={entries[i]} track={track} incoming={data.boundaries[i - 1]} outgoing={data.boundaries[i]} />
  </Sequence>)}
  {data.audio.map((cue, i) => <Sequence key={`cue-${i}`} from={cue.startFrame} durationInFrames={cue.durationFrames}>
    <CueAudio cue={cue} tracks={data.scenes} />
  </Sequence>)}
  {data.scenes.map((track, i) => <Sequence key={`speech-${i}`} from={track.start} durationInFrames={track.contentFrames}>
    <Speech entry={entries[i]} safeArea={data.safeArea} />
  </Sequence>)}
  {showSafeArea && <div style={{position: "absolute", pointerEvents: "none", border: "3px dashed #00ff99",
    top: `${data.safeArea.top * 100}%`, right: `${data.safeArea.right * 100}%`,
    bottom: `${data.safeArea.bottom * 100}%`, left: `${data.safeArea.left * 100}%`}} />}
</AbsoluteFill>;

export const ScenePreview: React.FC<{data: TimelineData; entries: SceneEntry[]; index: number}> =
({data, entries, index}) => {
  const original = data.scenes[index];
  const track = {...original, start: 0, visualStart: 0, visualEnd: original.spanFrames};
  return <Timeline entries={[entries[index]]} data={{...data, totalFrames: track.spanFrames,
    scenes: [track], boundaries: [], audio: []}} />;
};

export const TimelineSlice: React.FC<{data: TimelineData; entries: SceneEntry[]; start: number}> =
({data, entries, start}) => <Sequence from={-start} durationInFrames={data.totalFrames}>
  <Timeline data={data} entries={entries} />
</Sequence>;
