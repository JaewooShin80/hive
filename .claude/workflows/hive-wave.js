export const meta = {
  name: 'hive-wave',
  description: 'HIVE Wave dispatch: per task stub (haiku) -> failing test (sonnet) -> minimal impl (sonnet); batches run in order',
  whenToUse: 'Called by /hive:execute step 4 with the Wave task breakdown as args',
  phases: [
    { title: 'Stub', detail: 'boilerplate only, when the task asks for it' },
    { title: 'Red', detail: 'write failing tests and confirm they fail' },
    { title: 'Green', detail: 'minimal implementation until the tests pass' },
  ],
}

// args: { wave, batches: [[task, ...], ...], models?: { stub, worker } }
// task: { id, title, files: [], stub: bool, test, context: [] } — context holds pointers, never code.
if (!args || !Array.isArray(args.batches)) {
  throw new Error('hive-wave: args.batches (array of task arrays) is required')
}

const models = { stub: 'haiku', worker: 'sonnet', ...(args.models || {}) }

const STATUS = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['DONE', 'DONE_WITH_CONCERNS', 'BLOCKED'] },
    files: { type: 'array', items: { type: 'string' } },
    test_output: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['status', 'files', 'notes'],
}

const pointers = (t) => [
  `Wave ${args.wave} — task ${t.id}: ${t.title}`,
  `Files: ${(t.files || []).join(', ')}`,
  `Test file: ${t.test}`,
  `Read these yourself for context: ${(t.context || []).join(', ') || 'none'}`,
].join('\n')

const PROMPTS = {
  stub: 'Create stub-level boilerplate only (signatures, types, schemas; no business logic) in the listed files. Follow existing naming. No hardcoded secrets.',
  test: 'TDD Red: write failing tests in the test file for this task\'s completion criteria (see the PLAN.md Wave section). Do not modify implementation files. Run the tests and confirm they FAIL; put the failing output in test_output. If they already pass or cannot run, return status BLOCKED with the reason.',
  impl: 'TDD Green: write the minimal implementation in the listed files so the test file passes. Run the failing tests first, implement, then re-run. No speculative code outside this task. Put the passing output in test_output. If you cannot make them pass, return status BLOCKED with the reason.',
}

const results = []
const blocked = []
const state = {}

async function step(stage, phaseTitle, model, t) {
  const r = await agent(`${PROMPTS[stage]}\n\n${pointers(t)}`, {
    label: `${t.id}:${stage}`, phase: phaseTitle, model, schema: STATUS,
  })
  const s = state[t.id] || (state[t.id] = { files: [], notes: [] })
  if (!r || r.status === 'BLOCKED') {
    blocked.push({ id: t.id, stage, notes: r ? r.notes : 'agent returned no result' })
    throw new Error(`${t.id} blocked at ${stage}`)
  }
  s.files.push(...(r.files || []))
  if (r.notes) s.notes.push(`${stage}: ${r.notes}`)
  return r
}

let skipped = []
for (let i = 0; i < args.batches.length; i++) {
  const batch = args.batches[i]
  log(`batch ${i + 1}/${args.batches.length}: ${batch.map((t) => t.id).join(', ')}`)
  await pipeline(
    batch,
    (_, t) => (t.stub ? step('stub', 'Stub', models.stub, t) : null),
    (_, t) => step('test', 'Red', models.worker, t),
    async (_, t) => {
      const r = await step('impl', 'Green', models.worker, t)
      const s = state[t.id]
      results.push({ id: t.id, status: r.status, files: [...new Set(s.files)], test_output: r.test_output || '', notes: s.notes.join(' | ') })
      return r
    },
  )
  if (blocked.length) {
    skipped = args.batches.slice(i + 1).flat().map((t) => t.id)
    log(`stopped after batch ${i + 1}: blocked ${blocked.map((b) => b.id).join(', ')}; skipped ${skipped.join(', ') || 'none'}`)
    break
  }
}

return { wave: args.wave, results, blocked, skipped }
