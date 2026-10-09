// Human acceptance evidence only. These helpers never infer listening or recognition.
export function validateHumanAssetAudit(record) {
  for (const kind of ['audible_label', 'picture_recognition']) {
    const status = record[`${kind}_audit`];
    if (!['PENDING', 'PASS', 'FAIL'].includes(status)) throw new TypeError(`Invalid ${kind} audit status`);
    if (status === 'PENDING') continue;
    const evidence = record.audit_evidence?.[kind];
    for (const key of ['tester', 'witness', 'device', 'os', 'browser', 'tested_commit', 'evidence_ref']) {
      if (typeof evidence?.[key] !== 'string' || !evidence[key].trim()) {
        throw new TypeError(`${record.id}: ${kind} needs ${key}`);
      }
    }
    if (typeof evidence.checked_at !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(evidence.checked_at)
      || !Number.isFinite(Date.parse(evidence.checked_at))) throw new TypeError('Audit needs a valid check time');
    if (typeof evidence.notes !== 'string' || (status === 'FAIL' && !evidence.notes.trim())) {
      throw new TypeError('Failed audit needs an explanation');
    }
    const expectedHash = record[kind === 'audible_label' ? 'audio_sha256' : 'symbol_sha256'];
    if (!/^[a-f0-9]{64}$/.test(expectedHash) || evidence.asset_sha256 !== expectedHash) {
      throw new TypeError('Human audit does not match these asset bytes; re-audit the changed asset');
    }
  }
  return record;
}

export function createHumanAssetResults(vocabulary, manifest) {
  return vocabulary.cards.map(card => {
    const source = manifest.assets.find(asset => asset.id === card.id);
    if (!source || source.label !== card.label || source.audio_path !== card.audio_path
      || source.symbol_path !== card.symbol_path) throw new TypeError('Asset provenance does not match vocabulary');
    return { id: card.id, label: card.label, audio_sha256: source.audio_sha256,
      symbol_sha256: source.symbol_sha256,
      audio: { status: 'PENDING', notes: '', checkedAt: null },
      symbol: { status: 'PENDING', notes: '', checkedAt: null } };
  });
}

export function resumeDeviceAssetResults(vocabulary, manifest, context) {
  const results = createHumanAssetResults(vocabulary, manifest);
  let completed = 0;
  for (const result of results) {
    const source = manifest.assets.find(asset => asset.id === result.id);
    validateHumanAssetAudit(source);
    for (const [kind, audit] of [['audio', 'audible_label'], ['symbol', 'picture_recognition']]) {
      if (source[`${audit}_audit`] === 'PENDING') continue;
      const previous = source.audit_evidence[audit];
      if (!['tester', 'witness', 'device', 'os', 'browser'].every(key => previous[key] === context[key])) {
        throw new TypeError('Recorded audit belongs to a different tester, witness or device/browser; perform a new audit.');
      }
      result[kind] = { status: source[`${audit}_audit`], notes: previous.notes, checkedAt: previous.checked_at,
        context: { tester: previous.tester, witness: previous.witness, device: previous.device,
          os: previous.os, browser: previous.browser, testedCommit: previous.tested_commit,
          physicallyDisconnected: previous.physical_disconnection_attested === true },
        restoredFrom: previous.evidence_ref };
      completed++;
    }
  }
  if (!completed) throw new TypeError('No recorded human asset audit is available to resume.');
  return results;
}
