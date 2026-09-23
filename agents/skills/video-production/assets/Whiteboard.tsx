import React from 'react';

export const progress = (frame: number, start: number, duration: number): number =>
  Math.max(0, Math.min(1, duration > 0 ? (frame - start) / duration : frame >= start ? 1 : 0));

export const DrawPath: React.FC<{
  d: string; progress: number; stroke?: string; strokeWidth?: number; fill?: string;
}> = ({d, progress: value, stroke = '#263238', strokeWidth = 3, fill = 'none'}) => {
  const p = progress(value, 0, 1);
  return <g>
    {fill !== 'none' && <path d={d} fill={fill} stroke="none" opacity={progress(p, 0.8, 0.2)} />}
    <path d={d} fill="none" stroke={stroke} strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round" pathLength={1}
      strokeDasharray="1 1" strokeDashoffset={1 - p} opacity={p > 0 ? 1 : 0} />
  </g>;
};

export const WhiteboardStage: React.FC<{
  children: React.ReactNode; width?: number; height?: number; background?: string;
  camera?: {x: number; y: number; width: number; height: number};
}> = ({children, width = 1920, height = 1080, background = '#fffdf7', camera}) => {
  const view = camera ?? {x: 0, y: 0, width, height};
  if (![width, height, view.width, view.height].every(v => Number.isFinite(v) && v > 0)
    || ![view.x, view.y].every(Number.isFinite)) throw new Error('Invalid whiteboard canvas or camera');
  return <svg width="100%" height="100%" viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`}
    preserveAspectRatio="xMidYMid meet" style={{background, position: 'absolute', inset: 0}}>
    {children}
  </svg>;
};

export type ChartSeries = {points: {x: number; y: number}[]; color: string};
export const LineChart: React.FC<{
  series: ChartSeries[]; xDomain: [number, number]; yDomain: [number, number];
  width: number; height: number; progress: number;
}> = ({series, xDomain, yDomain, width, height, progress: reveal}) => {
  if (![...xDomain, ...yDomain, width, height].every(Number.isFinite)
    || xDomain[1] <= xDomain[0] || yDomain[1] <= yDomain[0] || width <= 0 || height <= 0)
    throw new Error('Chart requires finite increasing domains and positive dimensions');
  const x = (v: number) => (v - xDomain[0]) / (xDomain[1] - xDomain[0]) * width;
  const y = (v: number) => height - (v - yDomain[0]) / (yDomain[1] - yDomain[0]) * height;
  return <g>
    <path d={`M0 0 V${height} H${width}`} fill="none" stroke="#263238" strokeWidth={3} />
    {series.map((line, i) => {
      if (line.points.some((p, j) => !Number.isFinite(p.x) || !Number.isFinite(p.y)
        || p.x < xDomain[0] || p.x > xDomain[1] || p.y < yDomain[0] || p.y > yDomain[1]
        || (j > 0 && p.x < line.points[j - 1].x))) throw new Error('Chart points must be ordered and within domains');
      const d = line.points.map((p, j) => `${j ? 'L' : 'M'}${x(p.x)} ${y(p.y)}`).join(' ');
      return d ? <DrawPath key={i} d={d} progress={reveal} stroke={line.color} strokeWidth={5} /> : null;
    })}
  </g>;
};
