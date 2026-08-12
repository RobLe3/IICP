import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { evaluate } from '../run-metaharness.mjs';

const fixture = {
  schema: 'metaharness-routing-dataset@1',
  models: ['small', 'large'],
  prices: { small: 1, large: 10 },
  rows: Array.from({ length: 20 }, (_, index) => ({
    id: `task-${index}`,
    embedding: index < 10 ? [1, 0] : [0, 1],
    scores: index < 10 ? { small: 0.9, large: 0.8 } : { small: 0.4, large: 0.9 },
  })),
};

test('every strategy selects only supplied eligible candidates', () => {
  const result = evaluate(fixture);
  for (const strategy of Object.values(result.strategies)) {
    for (const selected of Object.keys(strategy.selections)) {
      assert.equal(selected in fixture.prices, true, `${selected} was not supplied as eligible`);
    }
  }
});

test('threshold routing prefers the cheap sufficient specialist by task cluster', () => {
  const result = evaluate(fixture);
  assert.equal(result.strategies.learned_threshold_0_70.threshold_success_rate, 1);
  assert.deepEqual(result.strategies.learned_threshold_0_70.selections, { small: 10, large: 10 });
});

test('candidate projection excludes route and content fields', async () => {
  const sample = JSON.parse(await readFile(new URL('../sample-candidate-evidence-v0.json', import.meta.url)));
  const keys = [];
  JSON.stringify(sample, (key, value) => {
    if (key) keys.push(key.toLowerCase());
    return value;
  });
  for (const prohibited of ['endpoint', 'prompt', 'response', 'public_key', 'private_key', 'node_id', 'token']) {
    assert.equal(keys.includes(prohibited), false, `projection contains prohibited field ${prohibited}`);
  }
  assert.equal(sample.eligibility.filter_complete, true);
  assert.equal(sample.eligibility.ticketed_dispatch_required, true);
});
