import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { Router } from '@metaharness/router';

const EXPECTED_DATASET_SHA256 = '8cfbedb6120b69d229919f9bfd453a01e36ad88cbb2af9e1c47378728c4adc9e';
const SOURCE_COMMIT = '68402755f017e0df5f493c6ee608218420540d17';
const QUALITY_THRESHOLD = 0.7;

function parseArguments(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith('--') || value == null) throw new Error('use --dataset PATH [--output PATH]');
    result[name.slice(2)] = value;
  }
  if (!result.dataset) throw new Error('--dataset is required');
  return result;
}

function selectCheapest(ids, prices) {
  return [...ids].sort((left, right) => prices[left] - prices[right])[0];
}

function selectHighest(ids, scores) {
  return [...ids].sort((left, right) => scores[right] - scores[left])[0];
}

function record(records, strategy, selected, row, prices) {
  if (!(selected in row.scores)) throw new Error(`${strategy} selected an unknown or ineligible candidate`);
  const quality = row.scores[selected];
  const current = records[strategy] ?? {
    qualityTotal: 0,
    priceTotal: 0,
    successes: 0,
    selections: {},
  };
  current.qualityTotal += quality;
  current.priceTotal += prices[selected];
  current.successes += quality >= QUALITY_THRESHOLD ? 1 : 0;
  current.selections[selected] = (current.selections[selected] ?? 0) + 1;
  records[strategy] = current;
}

export function evaluate(dataset) {
  if (dataset.schema !== 'metaharness-routing-dataset@1' || dataset.rows.length !== 20) {
    throw new Error('unexpected MetaHarness dataset shape');
  }
  const ids = dataset.models;
  const prices = dataset.prices;
  const averages = Object.fromEntries(
    ids.map((id) => [id, dataset.rows.reduce((sum, row) => sum + row.scores[id], 0) / dataset.rows.length]),
  );
  const bestFixed = selectHighest(ids, averages);
  const cheapest = selectCheapest(ids, prices);
  const records = {};

  dataset.rows.forEach((row, heldOutIndex) => {
    const trainingRows = dataset.rows.filter((_, index) => index !== heldOutIndex);
    record(records, 'fixed_best_posthoc', bestFixed, row, prices);
    record(records, 'fixed_cheapest', cheapest, row, prices);
    record(records, 'learned_best', Router.fromExamples(trainingRows, prices, { k: 5 }).route(row.embedding).id, row, prices);
    record(
      records,
      'learned_threshold_0_70',
      Router.fromExamples(trainingRows, prices, { k: 5, qualityBar: QUALITY_THRESHOLD }).route(row.embedding).id,
      row,
      prices,
    );
    const oracle = selectHighest(ids, row.scores);
    record(records, 'oracle_best', oracle, row, prices);
    const clearing = ids.filter((id) => row.scores[id] >= QUALITY_THRESHOLD);
    record(records, 'oracle_threshold_0_70', clearing.length ? selectCheapest(clearing, prices) : oracle, row, prices);
  });

  const strategies = Object.fromEntries(
    Object.entries(records).map(([name, value]) => [name, {
      mean_quality: value.qualityTotal / dataset.rows.length,
      mean_price_per_mtok: value.priceTotal / dataset.rows.length,
      threshold_success_rate: value.successes / dataset.rows.length,
      selections: value.selections,
    }]),
  );
  return {
    schema: 'iicp.learned-routing-experiment-result.v0',
    source: {
      project: 'ruvnet/metaharness',
      commit: SOURCE_COMMIT,
      dataset: 'packages/bench/draco/runs/routing-dataset.json',
      dataset_sha256: `sha256:${EXPECTED_DATASET_SHA256}`,
      router_package: '@metaharness/router@0.4.0',
    },
    method: {
      rows: dataset.rows.length,
      validation: 'leave-one-out',
      neighbours: 5,
      quality_threshold: QUALITY_THRESHOLD,
      candidates_are_assumed_eligible: true,
    },
    average_model_quality: averages,
    best_fixed_candidate: bestFixed,
    strategies,
    limitations: [
      'The 20-row DRACO dataset is small and measures research-dossier quality, not general IICP traffic.',
      'Price per million tokens is a preference axis, not realized per-request cost because token counts are absent from this dataset.',
      'The experiment does not measure current IICP directory ordering, live runtime fitness, dispatch or cross-SDK behavior.',
    ],
  };
}

async function main() {
  const args = parseArguments(process.argv.slice(2));
  const bytes = await readFile(args.dataset);
  const digest = createHash('sha256').update(bytes).digest('hex');
  if (digest !== EXPECTED_DATASET_SHA256) throw new Error(`dataset digest mismatch: ${digest}`);
  const result = evaluate(JSON.parse(bytes.toString('utf8')));
  const rendered = `${JSON.stringify(result, null, 2)}\n`;
  if (args.output) await writeFile(args.output, rendered, 'utf8');
  else process.stdout.write(rendered);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
