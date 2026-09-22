import React from 'react';
import {DrawPath, progress as phase} from './Whiteboard';

type Kind = 'person' | 'house' | 'apartment' | 'coin' | 'key' | 'document' | 'clock' | 'arrow';
type Palette = {ink: string; accent: string; warm: string; skin: string};
type Shape = {d: string; fill?: string};
const defaults: Palette = {ink: '#263238', accent: '#559cad', warm: '#efbb57', skin: '#efc6a4'};

// Original 120 × 120 vector drawings. Path order is intentional reveal order.
export const DoodleAsset: React.FC<{
  kind: Kind; progress?: number; palette?: Partial<Palette>;
  mood?: 'neutral' | 'happy' | 'worried'; pose?: 'standing' | 'pointing' | 'walking';
}> = ({kind, progress = 1, palette, mood = 'neutral', pose = 'standing'}) => {
  const c = {...defaults, ...palette};
  let shapes: Shape[];
  switch (kind) {
    case 'house': shapes = [
      {d: 'M18 53 L60 18 L103 52 Z', fill: c.warm},
      {d: 'M25 53 L25 104 L96 104 L96 53', fill: '#f6e7ba'},
      {d: 'M54 104 V73 H73 V104', fill: c.accent},
      {d: 'M33 62 H46 V78 H33 Z M83 64 V80 M77 72 H90'},
    ]; break;
    case 'apartment': shapes = [
      {d: 'M25 105 V18 L94 20 V105 Z', fill: c.accent},
      {d: 'M34 31 H48 V45 H34 Z M65 31 H80 V45 H65 Z', fill: '#fffdf7'},
      {d: 'M34 55 H48 V69 H34 Z M65 55 H80 V69 H65 Z', fill: '#fffdf7'},
      {d: 'M53 104 V82 H70 V104'},
    ]; break;
    case 'coin': shapes = [
      {d: 'M61 16 C113 16 117 103 62 105 C7 105 6 17 61 16 Z', fill: c.warm},
      {d: 'M62 26 C102 26 102 95 62 95 C22 95 21 26 62 26 Z'},
      {d: 'M76 43 C48 31 37 59 61 60 C91 61 75 90 45 77 M61 31 V89'},
    ]; break;
    case 'key': shapes = [
      {d: 'M44 23 C71 22 73 62 47 63 L47 100 L34 100 L34 85 L25 85 L25 73 L34 73 L34 61 C10 49 18 24 44 23 Z', fill: c.warm},
      {d: 'M43 34 C56 34 56 49 43 49 C30 49 30 34 43 34 Z'},
    ]; break;
    case 'document': shapes = [
      {d: 'M29 15 H74 L95 36 V107 H29 Z', fill: '#fffdf7'},
      {d: 'M74 15 V36 H95 M42 51 H79 M42 65 H79 M42 79 H72 M42 92 H63'},
    ]; break;
    case 'clock': shapes = [
      {d: 'M60 14 C121 16 118 106 60 107 C1 105 2 14 60 14 Z', fill: '#fffdf7'},
      {d: 'M60 23 V31 M98 60 H90 M60 99 V91 M22 60 H30 M60 38 V61 L82 74'},
    ]; break;
    case 'arrow': shapes = [
      {d: 'M13 68 Q42 69 78 39 L66 27 L109 24 L104 66 L90 53 Q51 86 13 86 Z', fill: c.accent},
    ]; break;
    case 'person': shapes = [
      {d: 'M59 12 C84 10 84 43 61 46 C36 46 35 13 59 12 Z', fill: c.skin},
      {d: 'M45 49 L76 49 L81 81 L40 81 Z', fill: c.accent},
      {d: pose === 'walking' ? 'M48 82 L30 108 M70 82 L91 106' : 'M49 82 L46 110 M70 82 L74 110'},
      {d: pose === 'pointing' ? 'M76 54 L93 62 L110 39 M43 55 L27 78' : 'M43 55 L27 75 M77 55 L95 74'},
      {d: `M49 25 L50 26 M68 25 L69 26 ${mood === 'happy' ? 'M50 33 Q60 45 70 33' : mood === 'worried' ? 'M50 38 Q60 28 70 38 M45 20 L54 23 M65 23 L74 20' : 'M52 36 H67'}`},
    ]; break;
  }
  return <g>{shapes.map((shape, i) => <DrawPath key={i} {...shape} stroke={c.ink}
    progress={phase(progress * shapes.length, i, 1)} />)}</g>;
};
