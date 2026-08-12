import { createHash } from 'node:crypto';
import { readFile, rename, writeFile } from 'node:fs/promises';
import { Router } from '@metaharness/router';

const QUALITY_THRESHOLD = 0.8;
const MIN_COMPARABLE_SAMPLES = 2;

export function classifyEvidence(input = {}) {
  const state = {
    selected_supplied: true,
    selected_eligible: true,
    fresh: true,
    profile_state: 'match',
    samples: MIN_COMPARABLE_SAMPLES,
    ranker_error: false,
    score_valid: true,
    mode: 'normal',
    fallback_eligible: false,
    ...input,
  };
  if (state.ranker_error || !state.score_valid || !state.selected_supplied || !state.selected_eligible) return 'refuse';
  if (state.mode === 'exploration') return 'allow-and-annotate';
  if (state.mode === 'fallback') return state.fallback_eligible ? 'allow-fallback-and-annotate' : 'refuse';
  if (!state.fresh || state.profile_state === 'changed') return 'exclude-history';
  if (state.profile_state === 'missing' || state.samples < MIN_COMPARABLE_SAMPLES) return 'cold-start';
  return 'use-history';
}

function parseArguments(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith('--') || value == null) throw new Error('arguments use --name value pairs');
    args[key.slice(2)] = value;
  }
  if (!args.tasks || !args.backends || !args.output) {
    throw new Error('--tasks, --backends and --output are required');
  }
  return args;
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function candidateRef(alias) {
  return sha256(`iicp:candidate:v0\n${alias}`);
}

function executionProfileRef(backend, modelRecord) {
  const material = JSON.stringify({
    model: backend.model,
    digest: modelRecord.digest,
    parameter_size: modelRecord.details?.parameter_size,
    quantization: modelRecord.details?.quantization_level,
    format: modelRecord.details?.format,
    family: modelRecord.details?.family,
  });
  return `sha256:${sha256(`iicp-execution-profile-v1\0${material}`)}`;
}

function normalizeAnswer(value) {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
    if ((trimmed.startsWith('[') && trimmed.endsWith(']')) || (trimmed.startsWith('{') && trimmed.endsWith('}'))) {
      try { return normalizeAnswer(JSON.parse(trimmed)); } catch { /* keep as text */ }
    }
    return trimmed
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLocaleLowerCase('en')
      .replace(/[.]+$/, '');
  }
  if (Array.isArray(value)) return value.map(normalizeAnswer);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right)).map(([key, item]) => [key, normalizeAnswer(item)]));
  }
  return value;
}

export function scoreResponse(task, text) {
  let parsed;
  try { parsed = JSON.parse(text); } catch {
    return { quality: 0, correct: false, format_correct: false, observed_answer: null, output_sha256: sha256(text) };
  }
  const formatCorrect = parsed && typeof parsed === 'object' && !Array.isArray(parsed)
    && Object.keys(parsed).length === 1 && Object.hasOwn(parsed, 'answer');
  const observed = formatCorrect ? normalizeAnswer(parsed.answer) : null;
  const expected = normalizeAnswer(task.expected_answer);
  const correct = formatCorrect && JSON.stringify(observed) === JSON.stringify(expected);
  return { quality: correct ? 1 : 0, correct, format_correct: formatCorrect, observed_answer: observed, output_sha256: sha256(text) };
}

async function atomicWrite(path, document) {
  const temporary = `${path}.tmp`;
  await writeFile(temporary, `${JSON.stringify(document, null, 2)}\n`, 'utf8');
  await rename(temporary, path);
}

async function modelInventory(endpoint) {
  const response = await fetch(`${endpoint}/api/tags`, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error(`model inventory failed with HTTP ${response.status}`);
  const body = await response.json();
  return new Map(body.models.map((model) => [model.name, model]));
}

async function generate(endpoint, backend, task) {
  const started = performance.now();
  const response = await fetch(`${endpoint}/api/generate`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      model: backend.model,
      prompt: `Return a JSON object with exactly one field named answer. Do not include explanation.\n\nTask: ${task.prompt}`,
      format: 'json',
      stream: true,
      keep_alive: '30m',
      options: { temperature: 0, seed: 42, num_predict: 128 },
    }),
    signal: AbortSignal.timeout(120_000),
  });
  if (!response.ok || !response.body) throw new Error(`generation failed with HTTP ${response.status}`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let output = '';
  let firstContentMs = null;
  let terminal = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);
      if (event.response && firstContentMs == null) firstContentMs = performance.now() - started;
      output += event.response ?? '';
      if (event.done) terminal = event;
    }
  }
  if (buffer.trim()) {
    const event = JSON.parse(buffer);
    if (event.response && firstContentMs == null) firstContentMs = performance.now() - started;
    output += event.response ?? '';
    if (event.done) terminal = event;
  }
  if (!terminal) throw new Error('generation stream ended without a terminal event');
  const latencyMs = performance.now() - started;
  const evalSeconds = (terminal.eval_duration ?? 0) / 1_000_000_000;
  return {
    output,
    metrics: {
      latency_ms: Math.round(latencyMs * 100) / 100,
      ttft_ms: firstContentMs == null ? null : Math.round(firstContentMs * 100) / 100,
      prompt_tokens: terminal.prompt_eval_count ?? null,
      output_tokens: terminal.eval_count ?? null,
      output_tokens_per_second: evalSeconds > 0 ? Math.round((terminal.eval_count / evalSeconds) * 100) / 100 : null,
      load_ms: Math.round(((terminal.load_duration ?? 0) / 1_000_000) * 100) / 100,
    },
  };
}

async function collect(tasks, config, outputPath) {
  const inventory = await modelInventory(config.endpoint);
  const backends = config.backends.map((backend) => {
    const record = inventory.get(backend.model);
    if (!record) throw new Error(`required local model is not installed: ${backend.model}`);
    return {
      ...backend,
      candidate_ref: candidateRef(backend.alias),
      execution_profile_ref: executionProfileRef(backend, record),
      model_digest: record.digest,
      quantization: record.details?.quantization_level ?? null,
    };
  });

  let document = {
    schema: 'iicp.heterogeneous-routing-observations.v1',
    method: {
      task_fixture_sha256: `sha256:${sha256(JSON.stringify(tasks))}`,
      deterministic_seed: 42,
      temperature: 0,
      response_contract: 'JSON object with exactly one field named answer',
      external_monetary_cost: 0,
      ttft_source: 'first non-empty Ollama streaming response fragment',
    },
    backends,
    observations: [],
  };
  try {
    const existing = JSON.parse(await readFile(outputPath, 'utf8'));
    if (existing.schema === document.schema) {
      const expectedProfiles = backends.map((backend) => backend.execution_profile_ref);
      const existingProfiles = existing.backends.map((backend) => backend.execution_profile_ref);
      if (JSON.stringify(expectedProfiles) !== JSON.stringify(existingProfiles)) {
        throw new Error('refusing to resume after a backend execution-profile change');
      }
      const references = new Map(backends.map((backend) => [backend.alias, backend.candidate_ref]));
      for (const observation of existing.observations) {
        observation.candidate_ref = references.get(observation.backend_alias);
      }
      existing.backends = backends;
      document = existing;
    }
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const completed = new Set(document.observations.map((row) => `${row.task_id}\0${row.backend_alias}`));

  for (const task of tasks.tasks) {
    for (const backend of backends) {
      const key = `${task.id}\0${backend.alias}`;
      if (completed.has(key)) continue;
      const generated = await generate(config.endpoint, backend, task);
      const score = scoreResponse(task, generated.output);
      document.observations.push({
        task_id: task.id,
        category: task.category,
        subtype: task.subtype,
        difficulty: task.difficulty,
        embedding: task.embedding,
        backend_alias: backend.alias,
        candidate_ref: backend.candidate_ref,
        execution_profile_ref: backend.execution_profile_ref,
        ...score,
        ...generated.metrics,
      });
      await atomicWrite(outputPath, document);
      process.stderr.write(`${document.observations.length}/${tasks.tasks.length * backends.length} ${task.id} ${backend.alias} ${score.correct ? 'PASS' : 'FAIL'}\n`);
    }
  }
  const tasksById = new Map(tasks.tasks.map((task) => [task.id, task]));
  for (const observation of document.observations) {
    const task = tasksById.get(observation.task_id);
    const expected = normalizeAnswer(task.expected_answer);
    const observed = normalizeAnswer(observation.observed_answer);
    observation.correct = observation.format_correct && JSON.stringify(observed) === JSON.stringify(expected);
    observation.quality = observation.correct ? 1 : 0;
    observation.observed_answer = observed;
  }
  await atomicWrite(outputPath, document);
  return document;
}

function selectHighest(ids, scores, weights) {
  return [...ids].sort((left, right) => scores[right] - scores[left]
    || weights[left] - weights[right]
    || left.localeCompare(right))[0];
}

function selectLowest(ids, weights) {
  return [...ids].sort((left, right) => weights[left] - weights[right] || left.localeCompare(right))[0];
}

function observationMap(document) {
  return new Map(document.observations.map((row) => [`${row.task_id}\0${row.candidate_ref}`, row]));
}

function addRecord(records, strategy, selected, task, observations, aliases, oracleQuality) {
  const row = observations.get(`${task.id}\0${selected}`);
  if (!row) throw new Error(`${strategy} selected an unknown or unobserved candidate`);
  const record = records[strategy] ?? { selections: {}, quality: 0, success: 0, latency: 0, ttft: 0, ttft_count: 0, throughput: 0, throughput_count: 0, weight: 0, regret: 0 };
  record.selections[aliases[selected]] = (record.selections[aliases[selected]] ?? 0) + 1;
  record.quality += row.quality;
  record.success += row.correct ? 1 : 0;
  record.latency += row.latency_ms;
  if (row.ttft_ms != null) { record.ttft += row.ttft_ms; record.ttft_count += 1; }
  if (row.output_tokens_per_second != null) { record.throughput += row.output_tokens_per_second; record.throughput_count += 1; }
  record.weight += row.relative_compute_weight;
  record.regret += oracleQuality - row.quality;
  records[strategy] = record;
}

export function evaluate(tasks, document) {
  if (tasks.tasks.length !== 90 || document.observations.length !== 270) throw new Error('benchmark requires 90 tasks and 270 observations');
  const ids = document.backends.map((backend) => backend.candidate_ref);
  const aliases = Object.fromEntries(document.backends.map((backend) => [backend.candidate_ref, backend.alias]));
  const weights = Object.fromEntries(document.backends.map((backend) => [backend.candidate_ref, backend.relative_compute_weight]));
  const observations = observationMap(document);
  for (const row of document.observations) row.relative_compute_weight = weights[row.candidate_ref];
  const datasetRows = tasks.tasks.map((task) => ({
    id: task.id,
    embedding: task.embedding,
    scores: Object.fromEntries(ids.map((id) => [id, observations.get(`${task.id}\0${id}`).quality])),
  }));
  const averages = Object.fromEntries(ids.map((id) => [id, datasetRows.reduce((sum, row) => sum + row.scores[id], 0) / datasetRows.length]));
  const bestFixed = selectHighest(ids, averages, weights);
  const records = {};
  const decisions = [];

  datasetRows.forEach((row, heldOutIndex) => {
    const task = tasks.tasks[heldOutIndex];
    const trainingRows = datasetRows.filter((_, index) => index !== heldOutIndex);
    const currentDefault = ids[0];
    const metadataHeuristic = ids[Math.min(task.difficulty - 1, ids.length - 1)];
    const learned = Router.fromExamples(trainingRows, weights, { k: 7 }).route(row.embedding).id;
    const threshold = Router.fromExamples(trainingRows, weights, { k: 7, qualityBar: QUALITY_THRESHOLD }).route(row.embedding).id;
    const oracle = selectHighest(ids, row.scores, weights);
    const oracleQuality = row.scores[oracle];
    addRecord(records, 'current_configured_order', currentDefault, task, observations, aliases, oracleQuality);
    for (const id of ids) addRecord(records, `fixed_${aliases[id]}`, id, task, observations, aliases, oracleQuality);
    addRecord(records, 'metadata_heuristic', metadataHeuristic, task, observations, aliases, oracleQuality);
    addRecord(records, 'metaharness_learned', learned, task, observations, aliases, oracleQuality);
    addRecord(records, 'metaharness_threshold_cost', threshold, task, observations, aliases, oracleQuality);
    addRecord(records, 'offline_oracle', oracle, task, observations, aliases, oracleQuality);
    decisions.push({
      task_id: task.id,
      eligible_candidate_refs: ids,
      current_configured_order: currentDefault,
      metadata_heuristic: metadataHeuristic,
      metaharness_learned: learned,
      metaharness_threshold_cost: threshold,
      offline_oracle: oracle,
    });
  });

  const strategies = Object.fromEntries(Object.entries(records).map(([name, record]) => [name, {
    mean_quality: record.quality / tasks.tasks.length,
    task_success_rate: record.success / tasks.tasks.length,
    mean_latency_ms: record.latency / tasks.tasks.length,
    mean_ttft_ms: record.ttft_count ? record.ttft / record.ttft_count : null,
    mean_output_tokens_per_second: record.throughput_count ? record.throughput / record.throughput_count : null,
    mean_relative_compute_weight: record.weight / tasks.tasks.length,
    mean_routing_regret: record.regret / tasks.tasks.length,
    external_monetary_cost: 0,
    selections: record.selections,
  }]));
  return {
    schema: 'iicp.heterogeneous-routing-result.v1',
    method: {
      tasks: tasks.tasks.length,
      observations: document.observations.length,
      validation: 'leave-one-task-out',
      neighbours: 7,
      quality_threshold: QUALITY_THRESHOLD,
      minimum_comparable_samples: MIN_COMPARABLE_SAMPLES,
      candidates_are_already_eligible: true,
      semantic_quality_owner: 'experiment evaluator, not IICP directory or receipt',
      monetary_cost_note: 'All backends ran locally, so external monetary cost is zero; relative compute weight is a declared preference proxy, not a price claim.',
    },
    backend_refs: Object.fromEntries(document.backends.map((backend) => [backend.alias, {
      candidate_ref: backend.candidate_ref,
      execution_profile_ref: backend.execution_profile_ref,
      parameter_class_b: backend.parameter_class_b,
      relative_compute_weight: backend.relative_compute_weight,
    }])),
    average_backend_quality: Object.fromEntries(Object.entries(averages).map(([id, value]) => [aliases[id], value])),
    best_fixed_backend: aliases[bestFixed],
    strategies,
    decisions,
    limitations: [
      'The task fixture is synthetic and exact-match scored; it does not represent all IICP intents or subjective quality.',
      'The three local models span approximately 0.5B to 3.8B parameters, not the full public model ecosystem.',
      'Relative compute weight is a preference proxy. No energy meter or paid-token cost was available.',
      'Model execution was local and direct; IICP policy and dispatch safety are tested separately by the shared SDK contract.',
      'No result is a global node-quality score, directory reputation value or production routing recommendation.',
    ],
  };
}

async function main() {
  const args = parseArguments(process.argv.slice(2));
  const tasks = JSON.parse(await readFile(args.tasks, 'utf8'));
  const config = JSON.parse(await readFile(args.backends, 'utf8'));
  const observations = await collect(tasks, config, args.output);
  const result = evaluate(tasks, observations);
  if (args.result) await atomicWrite(args.result, result);
  else process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.stack ?? error.message);
    process.exitCode = 1;
  });
}
