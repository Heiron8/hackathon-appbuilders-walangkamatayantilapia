import React from 'react';
import {AbsoluteFill, Audio, Composition, OffthreadVideo, Sequence, registerRoot, staticFile, useCurrentFrame, interpolate} from 'remotion';
import {cameraState, captionCues, smoothProgress} from './editorial.mjs';

const base = {backgroundColor: '#101b2a', color: '#f4f7fc', fontFamily: 'Arial, sans-serif'};
const Scene = ({scene, title}) => {
  const frame = useCurrentFrame();
  const seconds = frame / 30;
  const outgoing = 1 - smoothProgress(seconds, scene.duration - 0.2, scene.duration);
  const reveal = smoothProgress(seconds, 0.12, 0.65);
  const camera = cameraState(scene.camera, seconds);
  const cue = captionCues(scene).find(c => seconds >= c.start && seconds < c.end);
  const cueOpacity = cue ? smoothProgress(seconds, cue.start, cue.start + 0.12) *
    (1 - smoothProgress(seconds, cue.end - 0.12, cue.end)) : 0;
  const box = scene.highlight;
  const outro = scene.card === 'outro';
  return <AbsoluteFill style={base}>
    {scene.media ? <div style={{position: 'absolute', left: 64, top: 30, width: 1152, height: 576, overflow: 'hidden', borderRadius: 8}}>
      <div style={{width: '100%', height: '100%', position: 'relative', transform: `scale(${camera.scale})`,
        transformOrigin: `${camera.x * 100}% ${camera.y * 100}%`}}>
        <OffthreadVideo muted src={staticFile(scene.media)} style={{width: '100%', height: '100%'}} />
        {box && <div style={{position: 'absolute', left: `${box.x * 100}%`, top: `${box.y * 100}%`, width: `${box.width * 100}%`,
          height: `${box.height * 100}%`, border: '3px solid #42dbc4', opacity: smoothProgress(seconds, scene.camera?.start ?? 0, (scene.camera?.start ?? 0) + 0.3),
          boxSizing: 'border-box', pointerEvents: 'none'}} />}
      </div>
    </div> : <div style={{margin: 'auto', width: 1000, textAlign: outro ? 'center' : 'left', opacity: outgoing}}>
      <div style={{color: '#42dbc4', fontSize: 22, letterSpacing: 3, marginBottom: 24, opacity: reveal}}>
        {scene.eyebrow ?? (outro ? 'THE RESULT' : 'PRODUCT DEMO')}
      </div>
      <div style={{fontSize: outro ? 62 : 68, fontWeight: 700, lineHeight: 1.12, opacity: reveal,
        transform: `translateY(${(1 - reveal) * 22}px)`}}>{scene.heading ?? title}</div>
      <div style={{height: 4, width: interpolate(smoothProgress(seconds, 0.3, 0.95), [0, 1], [0, outro ? 100 : 140]),
        backgroundColor: '#42dbc4', marginTop: 34, marginLeft: outro ? 'auto' : 0, marginRight: outro ? 'auto' : 0}} />
    </div>}
    {scene.warning && <div style={{position: 'absolute', top: 0, width: '100%', background: '#6b3d00', textAlign: 'center', fontSize: 20}}>{scene.warning}</div>}
    {cue && <div style={{position: 'absolute', bottom: 18, left: 100, right: 100, textAlign: 'center', fontSize: 32,
      lineHeight: 1.25, opacity: cueOpacity, transform: `translateY(${(1 - cueOpacity) * 5}px)`}}>{cue.text}</div>}
    {scene.audio && <Sequence from={Math.round((scene.narrationStart ?? 0) * 30)} layout="none"><Audio src={staticFile(scene.audio)} /></Sequence>}
  </AbsoluteFill>;
};
const Demo = ({scenes, title}) => {
  let offset = 0;
  return <AbsoluteFill style={base}>{scenes.map(scene => {
    const from = offset;
    offset += scene.duration * 30;
    return <Sequence key={scene.id} from={from} durationInFrames={scene.duration * 30}>
      <Scene scene={scene} title={title} />
    </Sequence>;
  })}</AbsoluteFill>;
};
const Root = () => <Composition id="Demo" component={Demo} fps={30} width={1280} height={720}
  durationInFrames={750} defaultProps={{title: '', scenes: []}}
  calculateMetadata={({props}) => ({durationInFrames: props.scenes.reduce((sum, s) => sum + s.duration * 30, 0)})} />;
registerRoot(Root);
