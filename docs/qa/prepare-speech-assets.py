# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline asset preparation only; no application/runtime dependency or voice verification."""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import wave
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'frontend/public'

# Original vector drawings, authored for this task. No external pictogram/font assets.
HEAD = '<circle cx="48" cy="25" r="12" fill="#f5c997"/><path d="M29 70V54a19 19 0 0 1 38 0v16" fill="#76b9e2"/>'
ART = {
    'no': '<circle cx="48" cy="44" r="28" fill="#fff1ef"/><path d="M31 27l34 34M65 27L31 61" stroke="#a52931" stroke-width="9"/>',
    'stop': '<path d="M32 10h32l22 22v26L64 80H32L10 58V32z" fill="#b12b35"/><path d="M34 57V33q0-7 6-7v17-24q0-7 6-7v29-23q0-7 6-7v31-22q0-7 6-7v28l5-7q7-6 9 1L59 62q-12 12-25-5z" fill="#fff" stroke="none"/>',
    'help': '<circle cx="48" cy="23" r="12" fill="#f5c997"/><path d="M33 68V49q15-17 30 0l13-22M33 48L19 63" fill="#76b9e2"/><path d="M71 16l6-4M83 24l6 2M62 12V6" stroke="#965518"/>',
    'repeat': '<path d="M70 32A27 27 0 0 0 22 42M26 58a27 27 0 0 0 48-10" fill="none" stroke="#256497" stroke-width="7"/><path d="M10 28l12 16 14-14M60 58l14-12 12 16" fill="none" stroke="#256497" stroke-width="7"/>',
    'something_else': '<rect x="12" y="21" width="24" height="35" rx="4" fill="#b4d7e9"/><circle cx="69" cy="39" r="19" fill="#f9d58d"/><path d="M37 70h31m-9-8 9 8-9 8" fill="none"/>',
    'yes': '<circle cx="48" cy="44" r="28" fill="#def1e6"/><path d="M29 44l13 14 25-29" fill="none" stroke="#24704d" stroke-width="9"/>',
    'i': HEAD + '<path d="M20 51l28 4-8-9m8 9-9 7" fill="none"/><circle cx="44" cy="24" r="1"/><circle cx="52" cy="24" r="1"/>',
    'want': '<circle cx="22" cy="25" r="11" fill="#f5c997"/><path d="M12 70V48q8-14 20-6l28 7" fill="#76b9e2"/><path d="M61 28l5-11 5 11 12 2-9 8 2 12-10-6-10 6 2-12-9-8z" fill="#f6cc68"/>',
    'not': '<circle cx="48" cy="44" r="28" fill="#fff1ef"/><path d="M28 64l40-40" stroke="#a52931" stroke-width="9"/>',
    'more': '<circle cx="28" cy="46" r="14" fill="#b5d5ec"/><circle cx="68" cy="46" r="14" fill="#b5d5ec"/><path d="M48 13v18M39 22h18" stroke="#256497" stroke-width="6"/>',
    'finished': '<rect x="20" y="17" width="56" height="56" rx="7" fill="#def1e6"/><path d="M32 46l11 11 22-25" fill="none" stroke="#24704d" stroke-width="7"/>',
    'eat': '<circle cx="35" cy="30" r="17" fill="#f5c997"/><path d="M18 76V62q18-20 36 0v14" fill="#76b9e2"/><path d="M42 37h12M67 31L49 40M66 30v-9m-6 9v-9m12 9v-9" fill="none"/>',
    'drink': '<circle cx="35" cy="30" r="17" fill="#f5c997"/><path d="M17 76V61q18-18 36 0v15" fill="#76b9e2"/><path d="M55 29h23l-5 27H60z" fill="#b5dfee"/><path d="M51 39h10"/>',
    'play': '<circle cx="37" cy="23" r="11" fill="#f5c997"/><path d="M31 38l16 15-15 23m13-23 20 13M31 40L14 54m17-14 21-8" fill="none" stroke-width="7"/><circle cx="74" cy="42" r="12" fill="#f5ce79"/>',
    'go': '<path d="M15 37h40V22l29 23-29 23V53H15z" fill="#6bb49c"/>',
    'rest': '<path d="M14 65h69M18 45v31M79 46v30" fill="none"/><rect x="19" y="44" width="60" height="21" rx="5" fill="#b5d5ec"/><circle cx="30" cy="37" r="9" fill="#f5c997"/><path d="M44 31h25l-3 14H42z" fill="#9abdd8"/><path d="M61 14h12l-12 9h12" fill="none"/>',
    'water': '<path d="M48 11q-25 31-25 46a25 25 0 0 0 50 0Q73 42 48 11z" fill="#83c9ec"/><path d="M32 56q0 12 10 15" fill="none" stroke="#fff"/>',
    'milk': '<path d="M27 32l10-16h24l10 16v44H27z" fill="#fff"/><path d="M27 32h44M37 16v16l12-10 12 10V16" fill="#b5d5ec"/><path d="M27 46h44v18H27z" fill="#b5d5ec"/>',
    'juice': '<path d="M25 27h43l-5 49H30z" fill="#f3b45c"/><path d="M44 44l9-31h16" fill="none"/><circle cx="73" cy="61" r="14" fill="#f5bd60"/><path d="M73 47v28M59 61h28" fill="none" stroke="#fff" stroke-width="2"/>',
    'apple': '<path d="M47 30c-30-18-39 11-28 32 13 27 25 13 29 13s18 14 30-13c11-21 2-50-31-32z" fill="#d76760"/><path d="M48 30l4-15"/><path d="M54 23q18 0 20-14Q58 5 54 23z" fill="#7bb48b"/>',
    'banana': '<path d="M19 28q18 44 58 11-5 46-38 36Q18 69 15 36z" fill="#f7d16a"/><path d="M20 36q11 36 48 18" fill="none" stroke="#a37927"/><path d="M18 26l-3-6m61 18 5-5"/>',
    'rice': '<path d="M15 43h66q-4 32-33 32T15 43z" fill="#b5d5ec"/><path d="M22 41q0-25 26-24t26 24z" fill="#fff"/><path d="M32 31l6 3m10-9 6 3m-9 10 6 3m10-8 6 3" stroke-width="2"/>',
    'bread': '<path d="M23 34q-10-22 25-22t25 22v41H23z" fill="#e9bb7c"/><path d="M30 36q-5-15 18-15t18 15v30H30z" fill="#ffdfaa"/>',
    'toy': '<circle cx="25" cy="23" r="11" fill="#c38b5d"/><circle cx="71" cy="23" r="11" fill="#c38b5d"/><circle cx="48" cy="34" r="23" fill="#d4a374"/><ellipse cx="48" cy="63" rx="21" ry="18" fill="#d4a374"/><circle cx="41" cy="31" r="2"/><circle cx="55" cy="31" r="2"/><ellipse cx="48" cy="41" rx="9" ry="6" fill="#f0cfaa"/><path d="M46 40h4M29 60l-12 5m50-5 12 5"/>',
    'ball': '<circle cx="48" cy="44" r="30" fill="#f3c573"/><path d="M18 44h60M48 14v60M29 21q23 23 0 47M67 21q-23 23 0 47" fill="none" stroke-width="3"/>',
    'music': '<path d="M36 60V26l36-9v34M36 32l36-9" fill="none" stroke-width="6"/><ellipse cx="26" cy="63" rx="11" ry="8" fill="#7d9fc5"/><ellipse cx="62" cy="54" rx="11" ry="8" fill="#7d9fc5"/>',
    'home': '<path d="M13 40L48 12l35 28M23 34v43h50V34" fill="#e9c69f"/><path d="M40 77V52h16v25" fill="#83badb"/><rect x="29" y="42" width="11" height="11" fill="#fff"/>',
    'school': '<path d="M18 34h60v43H18z" fill="#e9c69f"/><path d="M13 34L48 12l35 22" fill="#b0cde3"/><circle cx="48" cy="28" r="7" fill="#fff"/><path d="M48 24v4h4M40 77V58h16v19" fill="none"/><path d="M26 43h10v9H26zm34 0h10v9H60z" fill="#fff"/>',
    'outside': '<circle cx="72" cy="19" r="11" fill="#f5cf77"/><path d="M25 37v39M12 53h74" fill="none"/><path d="M10 46L25 18l15 28z" fill="#83b993"/><path d="M40 76q19-25 45-18" fill="none" stroke="#83b993" stroke-width="9"/>',
    'toilet': '<rect x="53" y="16" width="23" height="29" rx="4" fill="#fff"/><path d="M22 45h54q0 21-23 21v11H37V61Q22 57 22 45z" fill="#fff"/><path d="M18 44h62" stroke="#6a9ebf" stroke-width="6"/>',
    'parent': '<circle cx="34" cy="23" r="12" fill="#f5c997"/><path d="M17 76V51q16-20 32 0v25" fill="#84b69f"/><circle cx="65" cy="40" r="9" fill="#f5c997"/><path d="M54 76V59q11-14 22 0v17" fill="#f2c479"/><path d="M47 49l9 11"/>',
    'teacher': '<rect x="37" y="13" width="49" height="44" rx="4" fill="#cce0cf"/><path d="M49 25h23M49 35h17M62 57v18" fill="none"/><circle cx="22" cy="26" r="11" fill="#f5c997"/><path d="M11 76V50q11-16 23 0v26" fill="#83badb"/><path d="M31 45l21-8"/>',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthesize(library, cards):
    """Use documented synchronous PCM API; never OS/Microsoft/MBROLA voices."""
    lib = c.CDLL(str(library))
    lib.espeak_Info.argtypes = [c.POINTER(c.c_char_p)]
    lib.espeak_Info.restype = c.c_char_p
    version = lib.espeak_Info(None).decode('ascii')
    if version != '1.52.0':
        raise ValueError(f'Expected reviewed eSpeak NG 1.52.0, got {version}')
    lib.espeak_Initialize.argtypes = [c.c_int, c.c_int, c.c_char_p, c.c_int]
    lib.espeak_Initialize.restype = c.c_int
    rate = lib.espeak_Initialize(2, 0, str(library.parent).encode('utf8'), 0x8000)
    if rate <= 0:
        raise RuntimeError('eSpeak initialization failed')
    callback_type = c.CFUNCTYPE(c.c_int, c.POINTER(c.c_short), c.c_int, c.c_void_p)
    chunks = []

    @callback_type
    def collect(samples, count, events):
        if samples and count > 0:
            chunks.append(c.string_at(samples, count * 2))
        return 0

    lib.espeak_SetSynthCallback.argtypes = [callback_type]
    lib.espeak_SetSynthCallback.restype = None
    lib.espeak_SetSynthCallback(collect)
    lib.espeak_SetVoiceByName.argtypes = [c.c_char_p]
    lib.espeak_SetVoiceByName.restype = c.c_int
    lib.espeak_SetParameter.argtypes = [c.c_int, c.c_int, c.c_int]
    lib.espeak_SetParameter.restype = c.c_int
    lib.espeak_Synth.argtypes = [c.c_void_p, c.c_size_t, c.c_uint, c.c_int,
                                c.c_uint, c.c_uint, c.c_void_p, c.c_void_p]
    lib.espeak_Synth.restype = c.c_int
    lib.espeak_Terminate.argtypes = []
    lib.espeak_Terminate.restype = c.c_int
    try:
        if lib.espeak_SetVoiceByName(b'en-us') or lib.espeak_SetParameter(1, 145, 0):
            raise RuntimeError('English formant voice/rate unavailable')
        for card in cards:
            chunks.clear()
            text = card['label'].encode('utf8') + b'\0'
            if lib.espeak_Synth(text, len(text), 0, 1, 0, 1, None, None):
                raise RuntimeError(f"Synthesis failed: {card['id']}")
            path = PUBLIC / card['audio_path']
            path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(path), 'wb') as output:
                output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
                output.writeframes(b''.join(chunks))
    finally:
        lib.espeak_Terminate()
    return {'engine': 'eSpeak NG', 'version': version, 'voice': 'en-us (default formant)',
            'words_per_minute': 145, 'library_sha256': sha(library), 'sample_rate': rate,
            'source': 'https://github.com/espeak-ng/espeak-ng/tree/1.52.0',
            'source_download': 'https://github.com/espeak-ng/espeak-ng/archive/refs/tags/1.52.0.tar.gz'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True,
                        help='Local extracted eSpeak NG 1.52.0 library; not bundled in product')
    args = parser.parse_args()
    vocabulary = json.loads((ROOT / 'shared/vocabulary.json').read_text(encoding='utf8'))
    cards = vocabulary['cards']
    if vocabulary['version'] != 'tanaw-v1' or len(cards) != 32 or set(ART) != {x['id'] for x in cards}:
        raise ValueError('Canonical tanaw-v1/32-card drawing mismatch')
    for card in cards:
        if card['audio_path'] != f"audio/en/{card['id']}.wav" or card['symbol_path'] != f"symbols/{card['id']}.svg":
            raise ValueError('Noncanonical asset path')
    engine = synthesize(args.library.resolve(strict=True), cards)
    records = []
    for card in cards:
        path = PUBLIC / card['symbol_path']
        path.parent.mkdir(parents=True, exist_ok=True)
        svg = ('<!-- SPDX-License-Identifier: GPL-3.0-or-later; original Tanaw vector artwork -->\n'
               '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-labelledby="title">'
               f'<title id="title">{escape(card["label"])}</title>'
               '<rect width="96" height="96" rx="12" fill="#fff"/>'
               '<g stroke="#263746" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'
               + ART[card['id']] + '</g></svg>\n')
        path.write_text(svg, encoding='utf8')
        records.append({'id': card['id'], 'label': card['label'], 'order': card['order'],
                        'audio_path': card['audio_path'], 'audio_sha256': sha(PUBLIC / card['audio_path']),
                        'audio_source': 'Locally synthesized canonical English label; eSpeak NG default en-us formant',
                        'symbol_path': card['symbol_path'], 'symbol_sha256': sha(path),
                        'symbol_source': 'Original vector drawing generated by Codex for Tanaw; no copied pictograms',
                        'license': 'GPL-3.0-or-later', 'audible_label_audit': 'PENDING',
                        'picture_recognition_audit': 'PENDING'})
    manifest = {'vocabulary_version': vocabulary['version'], 'engine': engine,
                'asset_license': 'GPL-3.0-or-later', 'license_file': 'asset-licenses/GPL-3.0.txt',
                'human_audit': 'PENDING; file generation is not human intelligibility/recognition or offline proof',
                'assets': records}
    (PUBLIC / 'speech-assets.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    print('Prepared 32 WAVs and 32 original SVGs. Human/audio/offline audits PENDING.')


if __name__ == '__main__':
    main()
