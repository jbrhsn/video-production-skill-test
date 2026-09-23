import React from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

type Payload = {title?: string; label?: string; value?: string | number; items?: string[]; source?: string; accent?: string};
const panel = (accent: string) => ({background: "rgba(9,14,25,.92)", border: `2px solid ${accent}`, borderRadius: 24, boxShadow: "0 24px 80px rgba(0,0,0,.35)"});

export const EditorialPrimitive: React.FC<{generator: string; payload: Payload}> = ({generator, payload}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig(); const accent = payload.accent ?? "#74e0ff";
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 120}});
  const title = payload.title ?? payload.label ?? generator.replace(/-/g, " ");
  const body = payload.items?.length ? payload.items : [payload.value === undefined ? "Editorial evidence" : String(payload.value)];
  return <div data-editorial-generator={generator} style={{position: "absolute", inset: "10%", display: "grid", placeItems: "center", opacity: enter, transform: `translateY(${interpolate(enter, [0, 1], [36, 0])}px)`}}>
    <div style={{...panel(accent), width: "min(88%, 1200px)", padding: "6%", color: "white", fontFamily: "Arial, sans-serif"}}>
      <div style={{fontSize: 24, color: accent, letterSpacing: 3, textTransform: "uppercase"}}>{generator}</div>
      <div style={{fontSize: 68, fontWeight: 800, marginTop: 20, lineHeight: 1.04}}>{title}</div>
      <div style={{display: "flex", gap: 18, marginTop: 44, flexWrap: "wrap"}}>{body.map((item, index) => <div key={`${item}:${index}`} style={{flex: "1 1 180px", minHeight: 80, display: "grid", placeItems: "center", padding: 20, borderRadius: 14, background: `linear-gradient(135deg, ${accent}44, transparent)`, fontSize: 30, fontWeight: 700}}>{item}</div>)}</div>
      {payload.source && <div style={{marginTop: 30, fontSize: 20, color: "#c4d1e8"}}>Source: {payload.source}</div>}
    </div>
  </div>;
};

export const VisualEvent: React.FC<{event: {id: string; presentation: string; layers: Record<string, string[]>; sequence: string[]; purpose: string}}> = ({event}) => {
  const payload: Payload = {title: event.purpose, label: event.presentation, items: [...(event.layers.midground ?? []), ...(event.layers.foreground ?? [])].map(item => item.replace(/^code:/, ""))};
  return <div data-visual-event={event.id} data-presentation={event.presentation} style={{position: "absolute", inset: 0, background: event.presentation === "overlay" || event.presentation === "picture-in-picture" ? "transparent" : "#0a1020"}}>
    <EditorialPrimitive generator={event.presentation === "full-screen-editorial" ? "system" : event.presentation} payload={payload} />
  </div>;
};
