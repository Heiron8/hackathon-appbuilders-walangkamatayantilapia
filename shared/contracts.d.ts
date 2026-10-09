/** Integration types only. Runtime API validation belongs to LadlopezGit. */
export type CardId = 'no' | 'stop' | 'help' | 'repeat' | 'something_else' | 'yes' |
  'i' | 'want' | 'not' | 'more' | 'finished' | 'eat' | 'drink' | 'play' | 'go' |
  'rest' | 'water' | 'milk' | 'juice' | 'apple' | 'banana' | 'rice' | 'bread' |
  'toy' | 'ball' | 'music' | 'home' | 'school' | 'outside' | 'toilet' | 'parent' | 'teacher';

export interface RequestContext {
  request_id: string; // UUID
  revision: number; // nonnegative integer
  vocabulary_version: 'tanaw-v1';
  locale: 'en';
}
export interface ExpandRequest extends RequestContext { selected_card_ids: CardId[] }
export interface SuggestRequest extends RequestContext { question: string }
export interface ResponseContext {
  request_id: string;
  revision: number;
  vocabulary_version: 'tanaw-v1';
}
export type ExpandResponse = ResponseContext & { source_card_ids: CardId[] } & (
  { status: 'candidate'; text: string } | { status: 'unsupported'; text: null }
);
export interface SuggestResponse extends ResponseContext { card_ids: CardId[] }
export type ErrorCode = 'invalid_request' | 'vocabulary_mismatch' | 'request_too_large' |
  'ai_unavailable' | 'feature_disabled' | 'ai_busy' | 'ai_timeout' | 'invalid_ai_output';
export interface ApiError {
  request_id: string | null;
  error: { code: ErrorCode; message: string };
}
export interface HealthResponse {
  status: 'ok';
  vocabulary_version: 'tanaw-v1';
  ai: { state: 'ready' | 'unavailable' | 'warming' | 'unknown'; suggestions_enabled: false };
}

/** GabDeGuz implements this boundary; RobinKielll owns its UI integration. */
export type SpeechCapability = 'full_text' | 'cards_only' | 'unavailable';
export interface SpeechError { code: string; message: string }
export type SpeechResult = { ok: true } | { ok: false; stopped: true } |
  { ok: false; error: SpeechError };
export interface SpeechState {
  capability: SpeechCapability;
  playback: 'idle' | 'speaking' | 'stopped' | 'error';
  error: SpeechError | null;
  voice: { name: string; lang: string; voiceURI: string; localService: true } | null;
  cardsReady: boolean;
  missingClipIds: CardId[];
}
export interface SpeechService {
  speakText(text: string): Promise<SpeechResult>;
  speakCards(cardIds: CardId[]): Promise<SpeechResult>;
  stopSpeech(): void;
  getState(): SpeechState;
  subscribe(listener: (state: SpeechState) => void): () => void;
  dispose(): void;
}
