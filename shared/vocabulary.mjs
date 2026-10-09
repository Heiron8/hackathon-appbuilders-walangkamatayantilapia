const categories = new Set(['essential', 'core', 'actions', 'drinks', 'food', 'activities', 'places', 'people']);
const fields = ['audio_path', 'category', 'id', 'label', 'order', 'symbol_path'];
const hasFields = (value, keys) => value !== null && typeof value === 'object' &&
  !Array.isArray(value) && Object.keys(value).sort().join(',') === keys.join(',');

export function validateVocabulary(data) {
  if (!hasFields(data, ['cards', 'version']) || data.version !== 'tanaw-v1' ||
      !Array.isArray(data.cards) || data.cards.length !== 32) {
    throw new Error('Expected tanaw-v1 with exactly 32 cards');
  }
  const seen = new Set();
  data.cards.forEach((card, order) => {
    if (!hasFields(card, fields) || typeof card.id !== 'string' || !/^[a-z_]+$/.test(card.id) ||
        seen.has(card.id) || card.order !== order || typeof card.label !== 'string' ||
        !card.label.trim() || !categories.has(card.category) ||
        card.symbol_path !== `symbols/${card.id}.svg` || card.audio_path !== `audio/en/${card.id}.wav`) {
      throw new Error('Invalid vocabulary card, order or local asset path');
    }
    seen.add(card.id);
  });
  return data;
}
