import { useEffect, useLayoutEffect, useReducer, useRef, useState } from 'react';
import { cardsById, vocabulary } from './vocabulary.js';
import { getSpeechState, initializeSpeech, speakCards, stopSpeech, subscribeSpeech } from './speech/index.mjs';
import { initialMessage, MAX_SELECTED_CARDS, updateMessage } from './message-state.mjs';
import Picture, { DesignIcon } from './Picture.jsx';
import './App.css';

const knownIds = new Set(cardsById.keys());
const defaultSpeechConfiguration = Object.freeze({ verifiedVoiceURI: null, availableClipIds: [] });
const speechRuntime = { getSpeechState, initializeSpeech, speakCards, stopSpeech, subscribeSpeech };
const reduceMessage = (state, action) => updateMessage(state, action, knownIds);

function WordPreview({ card }) {
  return <li className={`message-token ${['something_else', 'finished', 'repeat', 'banana', 'outside', 'school', 'teacher', 'parent'].includes(card.id) ? 'wide-token' : ''}`}><span className="token-tablet-picture"><Picture id={card.id} size={48} token /></span>
    <span className="token-phone-picture"><Picture id={card.id} size={32} /></span><span>{card.label}</span></li>;
}

function WordEditor({ selectedIds, dispatch, onDone }) {
  const heading = useRef(null);
  const controls = useRef({});
  const pendingFocus = useRef(null);
  useLayoutEffect(() => {
    const intent = pendingFocus.current;
    if (!intent) return;
    pendingFocus.current = null;
    const index = Math.min(intent.index, selectedIds.length - 1);
    const preferred = controls.current[`${index}-${intent.control}`];
    const fallback = controls.current[`${index}-remove`];
    (preferred && !preferred.disabled ? preferred : fallback ?? heading.current)?.focus({ preventScroll: true });
  }, [selectedIds]);
  function removeWord(index) {
    pendingFocus.current = { index, control: 'remove' };
    dispatch({ type: 'remove', index });
  }
  function moveWord(index, direction) {
    pendingFocus.current = { index: index + direction, control: direction < 0 ? 'earlier' : 'later' };
    dispatch({ type: 'move', index, direction });
  }
  useEffect(() => { heading.current?.focus({ preventScroll: true }); }, []);
  return <section className="word-editor" aria-labelledby="edit-title">
    <h2 id="edit-title" ref={heading} tabIndex={-1}>Edit words</h2><p>Remove or move a word.</p>
    <ol className="editor-list">
      {selectedIds.map((id, index) => <li key={`${index}-${id}`}>
        <div className="editor-word"><Picture id={id} size={48} token /><strong>{cardsById.get(id).label}</strong>
          <button className="remove" ref={element => { controls.current[`${index}-remove`] = element; }} aria-label={`Remove ${cardsById.get(id).label}, word ${index + 1}`}
            onClick={() => removeWord(index)}>×</button></div>
        <div className="move-actions">
          <button ref={element => { controls.current[`${index}-earlier`] = element; }} disabled={index === 0} aria-label={`Move ${cardsById.get(id).label}, word ${index + 1}, earlier`}
            onClick={() => moveWord(index, -1)}>Move earlier</button>
          <button ref={element => { controls.current[`${index}-later`] = element; }} disabled={index === selectedIds.length - 1} aria-label={`Move ${cardsById.get(id).label}, word ${index + 1}, later`}
            onClick={() => moveWord(index, 1)}>Move later</button>
        </div>
      </li>)}
    </ol>
    <button className="primary" onClick={onDone}>Done</button>
  </section>;
}

function ClearConfirmation({ onCancel, onClear }) {
  const dialog = useRef(null);
  useEffect(() => { if (!dialog.current.open) dialog.current.showModal(); }, []);
  function cancel() { dialog.current.close(); onCancel(); }
  function clear() { dialog.current.close(); onClear(); }
  return <dialog ref={dialog} className="clear-dialog" onCancel={event => { event.preventDefault(); cancel(); }} aria-labelledby="clear-title">
    <h2 id="clear-title">Clear your message?</h2><p>This removes all selected pictures.</p>
    <div className="dialog-actions"><button autoFocus onClick={cancel}>Keep message</button>
      <button className="destructive" onClick={clear}>Clear message</button></div>
  </dialog>;
}

function SpeechStatus({ state }) {
  const message = state.error?.message ?? (state.playback === 'speaking' ? 'Speaking your selected words.'
    : state.playback === 'stopped' ? 'Audio stopped. Your pictures are still here.'
      : state.capability === 'full_text' ? 'Local voice configured. Speech starts only when you press Speak.'
        : state.capability === 'cards_only' ? 'Selected-card audio available. Full sentence voice is unavailable.'
          : 'Speech is unavailable. No tested local voice or complete card audio is configured.');
  return <p className={`speech-status ${state.error ? 'error-status' : ''}`} role="status">{message}</p>;
}

export default function App({ speechConfiguration = defaultSpeechConfiguration, speech = speechRuntime }) {
  const [message, dispatch] = useReducer(reduceMessage, initialMessage);
  const [mode, setMode] = useState('pictures');
  const [editing, setEditing] = useState(false);
  const [clearOpen, setClearOpen] = useState(false);
  const [speechOptions, setSpeechOptions] = useState(false);
  const [speechState, setSpeechState] = useState(() => speech.getSpeechState());
  const editOpener = useRef(null);
  const clearButton = useRef(null);
  const board = useRef(null);
  const boardHeading = useRef(null);
  const companion = useRef(null);
  const selectedIds = message.selectedIds;
  const hasMessage = selectedIds.length > 0;
  const speaking = speechState.playback === 'speaking';
  const canSpeak = hasMessage && speechState.capability !== 'unavailable';

  useEffect(() => {
    speech.initializeSpeech({ vocabulary, ...speechConfiguration });
    const unsubscribe = speech.subscribeSpeech(setSpeechState);
    return () => { unsubscribe(); speech.stopSpeech(); };
  }, [speech, speechConfiguration]);

  function revealCompanion() {
    if (window.matchMedia('(max-width: 767px)').matches) {
      requestAnimationFrame(() => companion.current?.scrollIntoView({ block: 'start', behavior: 'instant' }));
    }
  }
  function changeMode(next) {
    setMode(next); setEditing(false); setSpeechOptions(false);
    if (next === 'review') revealCompanion();
    else requestAnimationFrame(() => board.current?.scrollIntoView({ block: 'start', behavior: 'instant' }));
  }
  function finishEditing() {
    setEditing(false);
    const opener = editOpener.current;
    const focusTarget = hasMessage && opener && !opener.disabled ? opener : boardHeading.current;
    focusTarget?.focus({ preventScroll: true });
    if (window.matchMedia('(max-width: 767px)').matches) board.current?.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  function closeClear(cleared = false) {
    setClearOpen(false);
    if (cleared) requestAnimationFrame(() => boardHeading.current?.focus({ preventScroll: true }));
    else clearButton.current?.focus({ preventScroll: true });
  }
  function playSelected() {
    if (canSpeak) void speech.speakCards([...selectedIds]);
  }

  return <main className="tanaw-shell">
    <header className="navigation">
      <div className="identity"><DesignIcon name="identity" /><strong>TANAW</strong><span>A little picture. A clear voice.</span></div>
      <nav aria-label="Communication views">
        <button className={mode === 'pictures' ? 'active' : ''} aria-current={mode === 'pictures' ? 'page' : undefined}
          onClick={() => changeMode('pictures')}>Pictures</button>
        <button className={mode === 'review' ? 'active' : ''} aria-current={mode === 'review' ? 'page' : undefined}
          onClick={() => changeMode('review')}>Review</button>
        <button disabled title="Conversation is unavailable for the MVP">Conversation</button>
      </nav>
    </header>

    <section className="essentials" aria-label="Quick communication pictures">
      {vocabulary.cards.slice(0, 5).map(card => <button key={card.id} className="essential-card"
        onClick={() => dispatch({ type: 'append', id: card.id })} aria-label={`Add ${card.label}`}>
        <Picture id={card.id} size={32} essential /><span>{card.label}</span>
      </button>)}
    </section>

    <section className="composer" aria-labelledby="message-title">
      <div className="composer-heading"><div><h1 id="message-title">Your message</h1><span>{selectedIds.length} / {MAX_SELECTED_CARDS}{message.notice ? ' · Full' : ''}</span></div>
        <div className="composer-utilities"><button disabled={!hasMessage} onClick={() => dispatch({ type: 'undo' })}>Undo</button>
          <button ref={clearButton} disabled={!hasMessage} onClick={() => setClearOpen(true)}>Clear</button>
          <button className="tablet-edit" disabled={!hasMessage} onClick={event => { editOpener.current = event.currentTarget; setEditing(true); revealCompanion(); }}>Edit words</button></div>
      </div>
      <div className="composer-body">
        <div className="message-preview" tabIndex={hasMessage ? 0 : undefined} role="region" aria-label="Selected pictures in message order. Scroll to review longer messages.">
          {hasMessage ? <ol>{selectedIds.map((id, index) => <WordPreview key={`${index}-${id}`} card={cardsById.get(id)} />)}</ol>
            : <p className="empty-message">Tap a picture to start your message.</p>}
        </div>
        <div className="speech-actions">
          {speaking ? <button className="primary speak" onClick={() => speech.stopSpeech()}><DesignIcon name="speaker" />Stop audio</button>
            : <button className="primary speak" disabled={!canSpeak} onClick={playSelected}><DesignIcon name="speaker" />
              {speechState.capability === 'unavailable' && hasMessage ? 'Speech unavailable' : 'Speak'}</button>}
          <button className="phone-edit" disabled={!hasMessage} onClick={event => { editOpener.current = event.currentTarget; setEditing(true); revealCompanion(); }}>Edit words</button>
        </div>
      </div>
    </section>

    <div className="workspace">
      <section className="picture-board" ref={board} aria-labelledby="board-title">
        <div className="board-heading"><h2 id="board-title" ref={boardHeading} tabIndex={-1}><span className="tablet-board-title">Choose a picture</span><span className="phone-brand">Tanaw · Pictures</span></h2><span>32 · scroll</span></div>
        <div className="board-scroll" tabIndex={0} role="region" aria-label="All 32 communication pictures, in fixed order">
          <div className="picture-grid">
            {vocabulary.cards.map(card => {
              const selected = selectedIds.includes(card.id);
              return <button className={`aac-card tone-${card.order < 5 ? 'peach' : card.order < 16 ? 'blue' : card.order < 25 ? 'warm' : 'surface'} ${selected ? 'selected' : ''}`}
                key={card.id} data-card-id={card.id} aria-pressed={selected} aria-label={`Add ${card.label}${selected ? ', already in message' : ''}`}
                onClick={() => dispatch({ type: 'append', id: card.id })}>
                <Picture id={card.id} /><span>{card.label}</span>
                {selected ? <span className="selected-check"><DesignIcon name="check" /></span> : null}
              </button>;
            })}
          </div>
        </div>
        <p className="visually-hidden">Scroll for more pictures. Each tap adds a word.</p>
      </section>

      <aside className="companion" ref={companion} aria-label={editing ? 'Selected word editing' : 'Optional sentence assistance'}>
        {message.notice ? <p className="selection-notice" role="status">{message.notice}</p> : null}
        {editing ? <WordEditor selectedIds={selectedIds} dispatch={dispatch} onDone={finishEditing} /> : <>
          <h2>{mode === 'review' ? 'Review message' : 'Sentence help'}</h2>
          <p>{mode === 'review' ? 'Your selected pictures are your original message.' : 'Optional wording for your message.'}</p>
          <button disabled>Improve sentence</button>
          <p className="assistance-status">Sentence assistance is unavailable. Your pictures stay ready for direct speech.</p>
          {mode === 'review' ? <button onClick={() => changeMode('pictures')}>Back to pictures</button> : null}
          <button aria-expanded={speechOptions} onClick={() => setSpeechOptions(value => !value)}>Speech options</button>
          {speechOptions ? <section className="speech-options" aria-label="Speech setup information">
            <h3>Caregiver speech setup</h3>
            <p>A local English voice must be checked with the internet disconnected before it is configured. Bundled card audio also needs verification.</p>
            <p>{speechState.voice ? `Configured voice: ${speechState.voice.name}.` : 'No verified local voice is configured.'}</p>
            <p>{speechState.cardsReady ? 'Complete card audio is configured.' : 'Complete card audio is not configured.'}</p>
          </section> : null}
          <SpeechStatus state={speechState} />
          {!speaking && ['stopped', 'error'].includes(speechState.playback) && canSpeak
            ? <button onClick={playSelected}>Replay audio</button> : null}
          <p className="quiet-note">Nothing speaks automatically.</p>
        </>}
      </aside>
    </div>
    {clearOpen ? <ClearConfirmation onCancel={closeClear} onClear={() => { dispatch({ type: 'clear' }); closeClear(true); }} /> : null}
  </main>;
}
