import React from "react";
import {useVideoConfig} from "remotion";
import {DESIGN_TOKENS} from "./design-tokens";

export type Word = {word: string; start: number; end: number};

// Group by phrase, pause, and a conservative character budget. Pixel inspection
// remains necessary for the chosen font/language; this is not font measurement.
export const groupWords = (words: Word[], budget: number, maxWords: number) => {
  const groups: {first: number; words: Word[]}[] = [];
  let first = 0;
  let group: Word[] = [];
  for (let i = 0; i < words.length; i++) {
    const previous = words[i - 1];
    const characters = group.reduce((sum, w) => sum + w.word.length + 1, 0);
    if (group.length && (group.length >= maxWords || characters + words[i].word.length > budget
      || /[.!?;:]$/.test(previous.word) || words[i].start - previous.end > .35)) {
      groups.push({first, words: group}); group = []; first = i;
    }
    group.push(words[i]);
  }
  if (group.length) groups.push({first, words: group});
  return groups;
};

// Times are seconds relative to narration, independent of visual transition time.
export const WordCaptions: React.FC<{words: Word[]; time: number; highlight?: boolean;
  safeArea?: {left: number; right: number; bottom: number; top: number}}> =
({words, time, highlight = true, safeArea}) => {
  const {width, height} = useVideoConfig();
  const vertical = height > width;
  const tokens = DESIGN_TOKENS.captions as typeof DESIGN_TOKENS.captions & {
    fontScale?: number; paddingX?: number; paddingY?: number; bottomInset?: number};
  const fallback = {left: .08, right: vertical ? .12 : .08, bottom: tokens.bottomInset ?? (vertical ? .18 : .12), top: .08};
  const area = safeArea ? {...safeArea, bottom: Math.max(safeArea.bottom, tokens.bottomInset ?? 0)} : fallback;
  const fontSize = Math.min(width, height) * (tokens.fontScale ?? (vertical ? .044 : .038));
  const budget = Math.max(8, Math.floor(width * (1 - area.left - area.right) / (fontSize * .6)));
  const active = words.findIndex((word) => time >= word.start && time < word.end);
  if (active < 0) return null;
  const group = groupWords(words, budget, vertical ? 6 : 9).find(g => active >= g.first && active < g.first + g.words.length);
  if (!group) return null;
  return <div style={{position: "absolute", bottom: `${area.bottom * 100}%`, left: `${area.left * 100}%`,
    right: `${area.right * 100}%`, textAlign: "center", fontFamily: DESIGN_TOKENS.captions.fontFamily,
    fontSize, lineHeight: 1.4, fontWeight: 700, whiteSpace: "pre-wrap", overflowWrap: "anywhere"}}>
    {group.words.map((word, index) =>
      <span key={group.first + index} style={{color: highlight && group.first + index === active ? DESIGN_TOKENS.captions.active : DESIGN_TOKENS.captions.text,
        background: DESIGN_TOKENS.captions.background,
        padding: `${tokens.paddingY ?? 4}px ${tokens.paddingX ?? 6}px`, borderRadius: DESIGN_TOKENS.captions.radius}}>
        {word.word + " "}
      </span>)}
  </div>;
};
