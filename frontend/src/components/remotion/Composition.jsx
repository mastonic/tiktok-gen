import React from 'react';
import { AbsoluteFill, Audio, Img, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';

const SubtitleText = ({ text }) => {
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
                lineHeight: '1.2'
            }}>
                {text}
            </span>
        </div>
    );
};

export const MyComposition = ({ clips, audioUrl, subtitles }) => {
    const { fps } = useVideoConfig();
    const clipDurationInFrames = 5 * fps; // 5 seconds per clip

    return (
        <AbsoluteFill style={{ backgroundColor: '#111' }}>
            {/* 1. Video Clips Sequence */}
            {clips && clips.map((clip, idx) => (
                <Sequence key={idx} from={idx * clipDurationInFrames} durationInFrames={clipDurationInFrames}>
                    <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                        {clip.endsWith('.mp4') ? (
                            <video src={clip} style={{ width: '100%', height: '100%', objectFit: 'cover' }} autoPlay loop muted />
                        ) : (
                            <Img src={clip} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
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
