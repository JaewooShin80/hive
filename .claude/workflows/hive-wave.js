export const meta = {
  name: 'hive-wave',
  description: 'HIVE Wave dispatch: per task optional stub (haiku) -> failing test (sonnet) -> minimal impl (sonnet); batches run in order with a test gate after each',
  whenToUse: 'Called by /hive:execute step 4 with the Wave task breakdown as args',
  phases: [
    { title: 'Stub', detail: 'boilerplate only, when the task asks for it' },
    { title: 'Red', detail: 'write failing tests and confirm they fail for the right reason' },
    { title: 'Green', detail: 'minimal implementation until the tests pass' },
    { title: 'Gate', detail: 'full test suite + out-of-scope change check per batch' },
  ],
}

// args: { wave, root, test_cmd, batches: [[task, ...], ...], models?: { stub, worker, gate } }
// root: absolute project root (agents start in the session cwd, which may be another repo).
// test_cmd: the project's test command, e.g. ".venv/bin/pytest -q" or "npm test --".
// task: { id, title, files: [], stub?: bool, test, context: [], depends_on?: [ids] }
//   context holds pointers, never code. Without depends_on, a task in a later batch is
//   skipped when anything earlier was blocked (batches imply dependency).
if (!args || !Array.isArray(args.batches)) {
  throw new Error('hive-wave: args.batches (array of task arrays) is required')
}
if (!args.root) throw new Error('hive-wave: args.root (absolute project root) is required')
if (!/^(\/|[A-Za-z]:[\\/])/.test(args.root)) throw new Error('hive-wave: args.root must be an absolute path')
if (!args.test_cmd) throw new Error('hive-wave: args.test_cmd (project test command) is required')

const models = { stub: 'haiku', worker: 'sonnet', gate: 'haiku', ...(args.models || {}) }

const STATUS = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['DONE', 'DONE_WITH_CONCERNS', 'ALREADY_SATISFIED', 'TEST_DEFECT', 'BLOCKED'] },
    files: { type: 'array', items: { type: 'string' } },
    test_output: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['status', 'files', 'notes'],
}

const GATE = {
  type: 'object',
  properties: {
    passed: { type: 'boolean' },
    summary: { type: 'string' },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['passed', 'summary', 'out_of_scope'],
}

const GUARD = [
  `Project root: ${args.root} — cd there first; every path below is relative to it.`,
  'Do NOT git commit. Do NOT edit WORKLOG.md, PLAN.md, ROADMAP.md or feature-list.json (the Advisor owns them).',
].join('\n')

const header = (t) => [
  GUARD,
  `Wave ${args.wave} — task ${t.id}: ${t.title}`,
  `Read these yourself for context: ${(t.context || []).join(', ') || 'none'}`,
].join('\n')

// Every command carries its own cd: a real run showed an agent executing the suite in
// the session cwd (another repo) when the prompt only said "cd there first".
const inRoot = (cmd) => `cd "${args.root}" && ${cmd}`
const own = (t) => inRoot(`${args.test_cmd} ${t.test}`)

const PROMPTS = {
  stub: (t) => [
    header(t),
    `You may write only: ${(t.files || []).join(', ')}`,
    'Create stub-level boilerplate only (signatures, types, schemas; bodies raise NotImplementedError or return a placeholder). No business logic. Do not create or modify any test file. Follow existing naming. No hardcoded secrets.',
  ].join('\n'),
  test: (t, why) => [
    header(t),
    `You may write only: ${t.test}`,
    `Implementation files (read-only for you): ${(t.files || []).join(', ')}`,
    'TDD Red: write tests in the test file for this task\'s completion criteria (see the PLAN.md Wave section).',
    'Respect the domain rules in PLAN/REQUIREMENTS (e.g. allowed state transitions); for UI/E2E tests wait for each state change before asserting.',
    `Run ONLY your own test file: \`${own(t)}\` (other tasks run in parallel; never run or fix their tests). Put the output in test_output.`,
    'Confirm the tests fail for the right reason: the behaviour is missing (assertion failure, missing symbol) — not a typo, bad fixture or broken import in the test itself.',
    'If the tests already pass because the behaviour already exists and meets the criteria, return ALREADY_SATISFIED. If you cannot write meaningful tests, return BLOCKED with the reason.',
    why ? `Your previous tests were judged defective by the implementer — fix them: ${why}` : '',
  ].filter(Boolean).join('\n'),
  impl: (t) => [
    header(t),
    `You may write only: ${(t.files || []).join(', ')}`,
    `Test file (read-only for you): ${t.test}`,
    `TDD Green: first run \`${own(t)}\` and record the failing output, then write the minimal implementation until it passes, then run it again. Put both outputs in test_output.`,
    'No speculative code outside this task.',
    'If the tests themselves are wrong (contradict PLAN/REQUIREMENTS, impossible fixture, race in the test), return TEST_DEFECT with the exact reason in notes instead of bending the implementation. If you cannot make them pass otherwise, return BLOCKED with the reason.',
  ].join('\n'),
}

const results = []
const blocked = []
const skipped = []
const gates = []
const state = {}

async function run(stage, phaseTitle, model, t, prompt) {
  const r = await agent(prompt, { label: `${t.id}:${stage}`, phase: phaseTitle, model, schema: STATUS })
  const s = state[t.id] || (state[t.id] = { files: [], notes: [], output: '' })
  if (r) {
    s.files.push(...(r.files || []))
    if (r.notes) s.notes.push(`${stage}: ${r.notes}`)
    if (r.test_output) s.output = r.test_output
  }
  return r
}

function block(t, stage, r) {
  const s = state[t.id] || { files: [], notes: [], output: '' }
  blocked.push({
    id: t.id, stage,
    notes: r ? r.notes : 'agent returned no result',
    files: [...new Set(s.files)], test_output: s.output,
  })
  return null
}

function done(t, status) {
  const s = state[t.id]
  results.push({ id: t.id, status, files: [...new Set(s.files)], test_output: s.output, notes: s.notes.join(' | ') })
  return { id: t.id, status }
}

async function runTask(t) {
  if (t.stub) {
    const r = await run('stub', 'Stub', models.stub, t, PROMPTS.stub(t))
    if (!r || r.status === 'BLOCKED') return block(t, 'stub', r)
  }
  let why = ''
  for (let attempt = 0; attempt < 2; attempt++) {
    const red = await run('test', 'Red', models.worker, t, PROMPTS.test(t, why))
    if (!red || red.status === 'BLOCKED' || red.status === 'TEST_DEFECT') return block(t, 'test', red)
    if (red.status === 'ALREADY_SATISFIED') return done(t, 'ALREADY_SATISFIED')
    const green = await run('impl', 'Green', models.worker, t, PROMPTS.impl(t))
    if (!green || green.status === 'BLOCKED') return block(t, 'impl', green)
    if (green.status !== 'TEST_DEFECT') return done(t, green.status)
    why = green.notes || 'unspecified test defect'
  }
  return block(t, 'impl', { notes: `tests still defective after one Red rerun: ${why}` })
}

const gatePrompt = (i, batch) => [
  GUARD,
  `Batch ${i + 1} of Wave ${args.wave} just finished. Verify it; do not modify any file.`,
  `1. Run the full suite exactly as: \`${inRoot(args.test_cmd)}\` — report pass/fail counts in summary.`,
  `2. Run \`${inRoot('git status --porcelain')}\` and list in out_of_scope every changed or new path that is not one of: ${batch.flatMap((t) => [...(t.files || []), t.test]).join(', ')} (ignore caches, virtualenvs and build output).`,
  'passed = the suite passed AND out_of_scope is empty.',
].join('\n')

for (let i = 0; i < args.batches.length; i++) {
  const batch = args.batches[i]
  const halted = gates.some((g) => !g.passed)
  const blockedIds = new Set(blocked.map((b) => b.id))
  const runnable = batch.filter((t) => {
    if (halted) return false
    if (Array.isArray(t.depends_on)) return !t.depends_on.some((d) => blockedIds.has(d) || skipped.includes(d))
    return blockedIds.size === 0
  })
  skipped.push(...batch.filter((t) => !runnable.includes(t)).map((t) => t.id))
  if (!runnable.length) continue
  log(`batch ${i + 1}/${args.batches.length}: ${runnable.map((t) => t.id).join(', ')}`)
  await pipeline(runnable, (_, t) => runTask(t).then((r) => r || { blocked: t.id }))
  const g = await agent(gatePrompt(i, runnable), { label: `gate:${i + 1}`, phase: 'Gate', model: models.gate, effort: 'low', schema: GATE })
  gates.push({ batch: i + 1, ...(g || { passed: false, summary: 'gate agent returned no result', out_of_scope: [] }) })
  if (!gates[gates.length - 1].passed) log(`gate ${i + 1} failed: ${gates[gates.length - 1].summary}`)
}

const total = args.batches.flat().length
if (results.length + blocked.length + skipped.length !== total) {
  throw new Error(`hive-wave: accounting mismatch — ${results.length} done + ${blocked.length} blocked + ${skipped.length} skipped != ${total} tasks`)
}

return { wave: args.wave, results, blocked, skipped, gates }
