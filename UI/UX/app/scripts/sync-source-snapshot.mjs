import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
// Refresh only frontend reference data. Original sources and datasets are never edited.
const app = fileURLToPath(new URL('../', import.meta.url));
const root = resolve(app, '../../..');
const records = path => readFileSync(resolve(root, path), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
function csv(path) {
  const rows = []; let row = [], field = '', quoted = false;
  const input = readFileSync(resolve(root, path), 'utf8').replace(/^\uFEFF/, '');
  for (let i = 0; i < input.length; i++) {
    const c = input[i];
    if (c === '"') { if (quoted && input[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted; }
    else if (c === ',' && !quoted) { row.push(field); field = ''; }
    else if (c === '\n' && !quoted) { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field || row.length) { row.push(field.replace(/\r$/, '')); rows.push(row); }
  const [headers, ...data] = rows;
  return data.filter(r => r.length === headers.length).map(r => Object.fromEntries(headers.map((h, i) => [h, r[i]])));
}
const provisions = records('dataset/processed/item7/provisions.jsonl');
const preferred = {
  LAB_CODE_2022: ['LAB_CODE_2022__art_292', 'LAB_CODE_2022__art_297', 'LAB_CODE_2022__art_298', 'LAB_CODE_2022__art_299'],
  RA_7394_1992: ['RA_7394_1992__art_68', 'RA_7394_1992__art_69'],
  DOLE_DO_147_15: ['DOLE_DO_147_15__rule_i_a__section_5'],
};
const snapshot = records('dataset/processed/item7/documents.jsonl').map(d => {
  const candidates = provisions.filter(p => p.document_id === d.document_id);
  const selected = preferred[d.document_id]
    ? candidates.filter(p => preferred[d.document_id].includes(p.provision_id))
    : [candidates.find(p => p.provision_answer_eligible) ?? candidates[0]].filter(Boolean);
  return {
    id: d.document_id, citation: d.citation, title: d.title, documentType: d.document_type.replaceAll('_', ' '),
    domain: d.domains.includes('consumer') ? 'consumer' : 'labor', issuer: d.issuer, date: d.approval_or_edition_date,
    officialUrl: d.official_source_url, retrievalUrl: d.retrieval_url, verificationStatus: d.verification_status,
    answerCandidate: d.document_answer_eligible_candidate, legalStatus: d.legal_status,
    lastChecked: d.status_as_of, freshness: d.freshness_rule ?? '', notes: d.notes ?? '',
    provisions: selected.map(p => ({
      id: p.provision_id, label: p.locator_label, heading: p.heading ?? '', text: p.verbatim_text,
      answerEligible: p.provision_answer_eligible, useMode: p.answer_use_mode,
      qualityFlags: p.quality_flags, locator: p.source_locator,
    })),
  };
});
const referrals = csv('dataset/processed/item9/referral_directory.csv').map(r => ({
  id: r.referral_id, agency: r.agency, service: r.service, url: r.portal_url || r.information_url,
  lastChecked: r.last_verified,
}));
writeFileSync(resolve(app, 'src/data/source-snapshot.ts'),
  '// Generated from IA project records by scripts/sync-source-snapshot.mjs. Do not hand-edit.\n' +
  'import type { SourceDocument } from "./library";\n' +
  'export const sourceSnapshot: SourceDocument[] = ' + JSON.stringify(snapshot, null, 2) + ';\n' +
  'export const referralSnapshot = ' + JSON.stringify(referrals, null, 2) + ';\n');
console.log('Synced ' + snapshot.length + ' documents and ' + referrals.length + ' referrals.');
const scopeText = readFileSync(resolve(root, 'project_legal_scope.md'), 'utf8');
const scopeSnapshot = {};
for (const domain of ['labor', 'consumer']) {
  const start = scopeText.indexOf(domain === 'labor' ? 'Labor domain' : 'Consumer domain');
  const end = domain === 'labor' ? scopeText.indexOf('Consumer domain') : scopeText.indexOf('Recto & Co. Legal provides');
  const part = scopeText.slice(start, end);
  const split = part.indexOf('Initially exclude:');
  const bullets = text => text.split(/\r?\n/).filter(line => line.startsWith('- ')).map(line => line.slice(2));
  scopeSnapshot[domain] = { included: bullets(part.slice(0, split)), excluded: bullets(part.slice(split)) };
}
writeFileSync(resolve(app, 'src/data/scope.ts'), '// Generated from project_legal_scope.md.\nexport const scopeSnapshot = ' + JSON.stringify(scopeSnapshot, null, 2) + ';\n');
