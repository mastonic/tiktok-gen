import { AbsoluteFill, Audio, Img, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import React, { useMemo } from 'react';

// Example props structure
export type ShortsProps = {
  clips: string[]; // List of URLs to video clips or images
  audioUrl?: string; // Voiceover URL
  subtitles?: { text: string; start: number; end: number }[]; // Subtitles with frame timings
};

const SubtitleText = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  // Simple pop effect
  const scale = Math.min(1.1, 1 + (frame * 0.05));
  const opacity = Math.min(1, frame * 0.1);

  return (
    <div style={{
      position: 'absolute',
      bottom: '20%',
      width: '100%',
      textAlign: 'center',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    }}>
      <span style={{
        color: '#FFFF00', // Yellow
        fontFamily: 'Inter, sans-serif',
        fontWeight: 900,
        fontSize: '80px',
        textTransform: 'uppercase',
        textShadow: '8px 8px 0px #000, -8px -8px 0px #000, 8px -8px 0px #000, -8px 8px 0px #000',
        transform: `scale(${scale})`,
        opacity: opacity,
        padding: '20px',
      }}>
        {text}
      </span>
    </div>
  );
};

export const MyComposition: React.FC<ShortsProps> = ({ clips, audioUrl, subtitles }) => {
  const { fps } = useVideoConfig();
  const clipDurationInFrames = 5 * fps; // 5 seconds per clip

  return (
    <AbsoluteFill style={{ backgroundColor: '#111' }}>
      {/* 1. Video Clips Sequence */}
      {clips.map((clip, idx) => (
        <Sequence key={idx} from={idx * clipDurationInFrames} durationInFrames={clipDurationInFrames}>
          <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {/* If it's an image for now, display as image, else use <Video> if MP4. For fal.ai it's MP4 */}
            {clip.endsWith('.mp4') ? (
              <video src={clip} style={{ width: '100%', height: '100%', objectFit: 'contain' }} autoPlay loop muted />
            ) : (
              <Img src={clip} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            )}
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* 2. Voiceover */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* 3. Subtitles */}
      {subtitles && subtitles.map((sub, idx) => (
        <Sequence key={`sub-${idx}`} from={sub.start} durationInFrames={sub.end - sub.start}>
          <SubtitleText text={sub.text} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
