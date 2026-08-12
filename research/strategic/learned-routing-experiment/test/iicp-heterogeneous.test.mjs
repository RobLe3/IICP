import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { classifyEvidence, evaluate, scoreResponse } from '../run-iicp-heterogeneous.mjs';

const fixtureUrl = new URL('../iicp-heterogeneous-tasks-v1.json', import.meta.url);
const backendAliases = ['small', 'medium', 'large'];
const candidateRefs = backendAliases.map((alias) => `candidate-${alias}`);

async function tasks() {
  return JSON.parse(await readFile(fixtureUrl, 'utf8'));
}

function syntheticObservations(document) {
  const backends = backendAliases.map((alias, index) => ({
    alias,
    candidate_ref: candidateRefs[index],
    execution_profile_ref: `profile-${alias}`,
    parameter_class_b: [0.5, 1.2, 3.8][index],
    relative_compute_weight: [0.5, 1.2, 3.8][index],
  }));
  const observations = [];
  for (const task of document.tasks) {
    for (const [index, backend] of backends.entries()) {
      const correct = index >= task.difficulty - 1;
      observations.push({
        task_id: task.id,
        candidate_ref: backend.candidate_ref,
        backend_alias: backend.alias,
        quality: correct ? 1 : 0,
        correct,
        latency_ms: 10 * (index + 1),
        ttft_ms: 2 * (index + 1),
        output_tokens_per_second: 30 / (index + 1),
      });
    }
  }
  return { schema: 'iicp.heterogeneous-routing-observations.v1', backends, observations };
}

test('task fixture is balanced, unique and immutable', async () => {
  const bytes = await readFile(fixtureUrl);
  const document = JSON.parse(bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), '91c7823e03a77f1d9ec1951c3393ba7a7ffec9eac11f3ab5b041e70bec01276a');
  assert.equal(document.tasks.length, 90);
  assert.deepEqual(document.categories, { structured: 30, factual: 30, reasoning: 30 });
  assert.equal(new Set(document.tasks.map((item) => item.id)).size, 90);
  assert.ok(document.tasks.every((item) => item.embedding.length === 11));
});

test('response scoring requires the bounded JSON contract and exact normalized answer', () => {
  const task = { expected_answer: 'Paris' };
  assert.equal(scoreResponse(task, '{"answer":"paris."}').quality, 1);
  assert.equal(scoreResponse({ expected_answer: 'Brasilia' }, '{"answer":"Brasília"}').quality, 1);
  assert.equal(scoreResponse(task, '{"answer":"Paris","reason":"known"}').quality, 0);
  assert.equal(scoreResponse(task, 'Paris').quality, 0);
});

test('all ten abuse and cold-start cases have the expected fail-closed disposition', async () => {
  const fixture = JSON.parse(await readFile(new URL('../routing-abuse-v1.json', import.meta.url), 'utf8'));
  assert.equal(fixture.cases.length, 10);
  for (const scenario of fixture.cases) {
    assert.equal(classifyEvidence(scenario.input), scenario.expected, scenario.id);
  }
});

test('SDK replay fixture is bound to the evaluated local result', async () => {
  const resultBytes = await readFile(new URL('../result-local-ollama-v1.json', import.meta.url));
  const replay = JSON.parse(
    await readFile(new URL('../candidate-ranker-benchmark-replay-v1.json', import.meta.url), 'utf8'),
  );
  assert.equal(
    replay.source_result_sha256,
    `sha256:${createHash('sha256').update(resultBytes).digest('hex')}`,
  );
  assert.equal(replay.cases.length, 10);
  assert.ok(replay.cases.every((item) => item.eligible_node_ids.includes(item.selected_node_id)));
});

test('MetaHarness and baselines select only supplied candidates', async () => {
  const document = await tasks();
  const result = evaluate(document, syntheticObservations(document));
  assert.equal(result.method.tasks, 90);
  assert.equal(result.method.observations, 270);
  for (const decision of result.decisions) {
    for (const field of ['current_configured_order', 'metadata_heuristic', 'metaharness_learned', 'metaharness_threshold_cost', 'offline_oracle']) {
      assert.ok(decision.eligible_candidate_refs.includes(decision[field]), `${field} escaped eligibility`);
    }
  }
  assert.ok(result.strategies.metaharness_threshold_cost.mean_relative_compute_weight <= result.strategies.metaharness_learned.mean_relative_compute_weight);
});
