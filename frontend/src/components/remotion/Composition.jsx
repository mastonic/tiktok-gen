import { AbsoluteFill, Audio, Img, Video, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';

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
            zIndex: 10
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

export const MyComposition = ({ clips, audioUrl, subtitles, isSquare = false }) => {
    const { fps, width, height } = useVideoConfig();
    const clipDurationInFrames = 5 * fps; // 5 seconds per clip

    const isMp4 = (url) => {
        if (!url) return false;
        return url.toLowerCase().split('?')[0].endsWith('.mp4');
    };

    return (
        <AbsoluteFill style={{ backgroundColor: '#000' }}>
            {/* 1. Video Clips Sequence */}
            {clips && clips.length > 0 ? clips.map((clip, idx) => (
                <Sequence key={idx} from={idx * clipDurationInFrames} durationInFrames={clipDurationInFrames}>
                    <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                        {isMp4(clip) ? (
                            <Video
                                src={clip}
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover'
                                }}
                            />
                        ) : (
                            <Img
                                src={clip}
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover'
                                }}
                            />
                        )}
                    </AbsoluteFill>
                </Sequence>
            )) : (
                <AbsoluteFill style={{ display: 'flex', backgroundColor: '#0a0f1c', alignItems: 'center', justifyContent: 'center', color: '#4b5563' }}>
                    Aucun clip disponible
                </AbsoluteFill>
            )}

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
