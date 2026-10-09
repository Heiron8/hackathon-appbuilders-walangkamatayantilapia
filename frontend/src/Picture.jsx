import manifest from './assets/figma/picture-slots.json';

const exports = import.meta.glob('./assets/figma/*.svg', { eager: true, query: '?url&no-inline', import: 'default' });

// Reproduce Figma layer positions without changing SVG bytes or intrinsic dimensions.
export default function Picture({ id, size = 64, token = false, essential = false }) {
  const slot = manifest.vocabulary_slots[id];
  let asset = slot.asset;
  let left = slot.left;
  let top = slot.top;
  let slotSize = 64;
  if (essential && size === 32) {
    asset = { no: 'imgGroup3', stop: 'imgGroup4', help: 'imgGroup5', repeat: 'imgGroup6', something_else: 'imgGroup7' }[id];
    slotSize = 32; left /= 2; top /= 2;
  }
  if (token && size === 48 && ['want', 'eat', 'apple'].includes(id)) {
    asset = { want: 'imgNativeIllustrationWantReaching', eat: 'imgGroup8', apple: 'imgGroup9' }[id];
    slotSize = 48;
    left *= 0.75; top *= 0.75;
  }
  return <span className="picture" style={{ width: size, height: size }} aria-hidden="true">
    <span className="picture-layer" style={{ width: slotSize, height: slotSize, transform: `scale(${size / slotSize})` }}>
      <img src={exports[`./assets/figma/${asset}.svg`]} alt="" style={{ left, top }} />
    </span>
  </span>;
}

export function DesignIcon({ name }) {
  const asset = { check: 'imgGroup', speaker: 'imgGroup10', identity: 'imgGroup2' }[name];
  return <span className={`design-icon icon-${name}`} aria-hidden="true">
    <img src={exports[`./assets/figma/${asset}.svg`]} alt="" />
  </span>;
}
