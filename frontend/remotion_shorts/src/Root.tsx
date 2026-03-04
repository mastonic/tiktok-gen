import "./index.css";
import { Composition } from "remotion";
import { MyComposition, ShortsProps } from "./Composition";

export const RemotionRoot: React.FC = () => {
  // Define default preview props
  const defaultProps: ShortsProps = {
    clips: [
      "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4",
      "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"
    ],
    audioUrl: "", // Add a valid URL to preview audio
    subtitles: [
      { text: "BIENVENUE", start: 0, end: 15 },
      { text: "SUR MA", start: 15, end: 30 },
      { text: "CHAÎNE !", start: 30, end: 60 },
    ],
  };

  return (
    <>
      <Composition
        id="ShortsAssemblageViral"
        component={MyComposition}
        durationInFrames={300} // 10 seconds total (30fps)
        fps={30}
        width={1080}
        height={1920} // 9:16 Vertical format
        defaultProps={defaultProps}
      />
    </>
  );
};
