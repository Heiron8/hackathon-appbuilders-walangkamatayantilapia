export const MAX_SELECTED_CARDS = 12;
export const initialMessage = Object.freeze({
  selectedIds: [], revision: 0, candidate: null, approvedText: null, requestId: null, notice: '',
});

// Every deliberate word change invalidates optional wording and pending responses.
function changed(state, selectedIds) {
  return { ...state, selectedIds, revision: state.revision + 1,
    candidate: null, approvedText: null, requestId: null, notice: '' };
}

export function updateMessage(state, action, knownIds) {
  switch (action.type) {
    case 'append':
      if (!knownIds.has(action.id)) return state;
      if (state.selectedIds.length === MAX_SELECTED_CARDS) {
        return { ...state, notice: 'Your message has 12 pictures. Remove a word or clear it before adding another.' };
      }
      return changed(state, [...state.selectedIds, action.id]);
    case 'undo':
      return state.selectedIds.length ? changed(state, state.selectedIds.slice(0, -1)) : state;
    case 'remove':
      return Number.isInteger(action.index) && action.index >= 0 && action.index < state.selectedIds.length
        ? changed(state, state.selectedIds.filter((_, index) => index !== action.index)) : state;
    case 'move': {
      const target = action.index + action.direction;
      if (!Number.isInteger(action.index) || ![-1, 1].includes(action.direction)
        || action.index < 0 || action.index >= state.selectedIds.length
        || target < 0 || target >= state.selectedIds.length) return state;
      const selectedIds = [...state.selectedIds];
      [selectedIds[action.index], selectedIds[target]] = [selectedIds[target], selectedIds[action.index]];
      return changed(state, selectedIds);
    }
    case 'clear':
      return state.selectedIds.length ? changed(state, []) : state;
    default:
      return state;
  }
}
