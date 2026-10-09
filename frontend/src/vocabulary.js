import data from '../../shared/vocabulary.json';
import contract from '../../shared/contracts.json';
import { validateVocabulary } from '../../shared/vocabulary.mjs';

export const vocabulary = validateVocabulary(data);
export const contracts = Object.freeze(contract);
export const cardsById = new Map(vocabulary.cards.map(card => [card.id, card]));
