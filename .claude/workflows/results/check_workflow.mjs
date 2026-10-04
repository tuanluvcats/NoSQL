// Offline self-test for ../verify-prompt1-analysis.js: runs the workflow with stub agent()/phase()/log()
// (no real agents, no network) and checks that checkers 3 and 4 come from the precomputed results.
// Usage: node .claude/workflows/results/check_workflow.mjs
import fs from 'node:fs'
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'

const path = process.argv[2] || fileURLToPath(new URL('../verify-prompt1-analysis.js', import.meta.url))
const src = fs.readFileSync(path, 'utf8').replace(/^export const meta/m, 'const meta')
const body = new Function('agent', 'phase', 'log', `return (async () => {\n${src}\n})()`)
const sleep = ms => new Promise(r => setTimeout(r, ms))

async function run(name, respond) {
  const calls = [], logs = [], events = []
  const t0 = Date.now()
  const agent = async (prompt, opts) => {
    calls.push({ label: opts.label, prompt, t: Date.now() - t0 })
    events.push(`start ${opts.label}`)
    const out = await respond(opts.label, prompt)
    events.push(`end ${opts.label}`)
    return out
  }
  const result = await body(agent, () => {}, m => logs.push(m))
  return { name, result, calls, logs, events }
}

const PRE = {}
{ // read PRE3/PRE4 straight from the JSON files for comparison
  const dir = fileURLToPath(new URL('./', import.meta.url))
  PRE.c = JSON.parse(fs.readFileSync(dir + 'task3_cassandra-41.json', 'utf8'))
  PRE.p = JSON.parse(fs.readFileSync(dir + 'task4_python-driver.json', 'utf8'))
}
const f = id => ({ id, claim: 'c', verdict: 'correct', severity: 'low', evidence: 'e', correction: 'x' })
const generic = label => ({ findings: [f(label + '-1')], facts_for_prompt2: [label + ' fact'] })
const shots = { ...generic('S'), figures: [], existing_schema: [{ table: 'customers', columns: [], primary_key_cql: 'unknown', evidence_figures: '', confidence: 'low' }], environment: { cassandra_version: '4.1', datacenter: 'datacenter1', host_port: 'localhost:9042', runs_in: 'docker', dbschema_version_edition: '?' } }

// A: every agent returns null (fallback to precomputed results)
const A = await run('all-null', async () => null)
// B: realistic outputs; local checks are slow so we can see that design-review does not wait for them
const B = await run('outputs', async (label, prompt) => {
  if (label === 'draft-screenshots') { await sleep(10); return shots }
  if (label === 'cassandra-41-localcheck') { await sleep(80); return { findings: PRE.c.findings.map(x => ({ ...x, claim: 'Q:' + x.id })), facts_for_prompt2: ['new C fact'] } }
  if (label === 'python-driver-localcheck') { await sleep(80); return { findings: PRE.p.findings.map(x => ({ ...x, claim: 'Q:' + x.id })), facts_for_prompt2: [] } }
  if (label === 'skeptic') return { verdicts: [] }
  return generic(label)
})
// D: local-check agents return an empty findings list (fallback to precomputed results)
const D = await run('localcheck-empty', async label => {
  if (label.endsWith('-localcheck')) return { findings: [], facts_for_prompt2: [] }
  if (label === 'draft-screenshots') return shots
  if (label === 'skeptic') return { verdicts: [] }
  return generic(label)
})
// C: local-check agents throw (fallback to precomputed results)
const C = await run('localcheck-throws', async label => {
  if (label.endsWith('-localcheck')) throw new Error('boom')
  if (label === 'draft-screenshots') return shots
  if (label === 'skeptic') return { verdicts: [] }
  return generic(label)
})

for (const R of [A, B, C, D]) {
  const labels = R.calls.map(c => c.label)
  assert.deepEqual([...labels].sort(), ['cassandra-41-localcheck', 'critic', 'dbschema', 'design-review', 'draft-screenshots', 'draft-text', 'python-driver-localcheck', 'rubric-consistency', 'skeptic'].sort(), R.name)
  for (const c of R.calls) {
    assert.ok(!/\$\{|\bundefined\b|\[object Object\]/.test(c.prompt), `${R.name}: unresolved text in ${c.label} prompt`)
  }
  const srcs = new Set(R.result.findings.map(x => x.src))
  assert.ok(srcs.has('cassandra-41') && srcs.has('python-driver'), R.name + ': C/P findings present')
  assert.ok(R.result.facts_for_prompt2.some(x => x.startsWith('[cassandra-41] ')), R.name + ': C facts present')
  const design = R.calls.find(c => c.label === 'design-review').prompt
  assert.ok(design.includes(PRE.c.facts_for_prompt2[0]) && design.includes('"id":"C9"'), R.name + ': design-review gets PRE3 facts and C8-C10')
}
// A and C: fallback uses precomputed results unchanged
for (const R of [A, C, D]) {
  const cs = R.result.findings.filter(x => x.src === 'cassandra-41').map(({ src, ...x }) => x)
  assert.deepEqual(cs, PRE.c.findings, R.name + ': C findings == precomputed')
  assert.equal(R.result.facts_for_prompt2.filter(x => x.startsWith('[python-driver] ')).length, PRE.p.facts_for_prompt2.length)
  assert.equal(R.logs.filter(m => m.includes('using the precomputed result unchanged')).length, 2, R.name + ': fallback logged twice')
}
// B: reconciled findings are used and precomputed facts are merged with new ones
const bc = B.result.findings.filter(x => x.src === 'cassandra-41')
assert.ok(bc.every(x => x.claim.startsWith('Q:')), 'B: reconciled C findings used')
const bcf = B.result.facts_for_prompt2.filter(x => x.startsWith('[cassandra-41] '))
assert.equal(bcf.length, PRE.c.facts_for_prompt2.length + 1, 'B: C facts = precomputed + new')
assert.ok(B.calls.find(c => c.label === 'critic').prompt.includes('Q:C1'), 'B: critic sees reconciled findings')
const designStart = B.events.indexOf('start design-review'), cassEnd = B.events.indexOf('end cassandra-41-localcheck')
assert.ok(designStart < cassEnd, 'B: design-review starts before the cassandra local check finishes')
// prompt content of the local checks
const pc = B.calls.find(c => c.label === 'cassandra-41-localcheck').prompt
const pp = B.calls.find(c => c.label === 'python-driver-localcheck').prompt
assert.ok(pc.includes('prompt1_answer.md') && pc.includes('"id":"C15"') && pc.includes('do not start Docker'))
assert.ok(pp.includes('venv_probe') && pp.includes('p4_probe.py') && pp.includes('"id":"P5"') && pp.includes('REAL WINDOWS'))
console.log('all assertions passed')
console.log('prompt sizes (chars):', Object.fromEntries(B.calls.map(c => [c.label, c.prompt.length])))
console.log('B event order:', B.events.join(' | '))
