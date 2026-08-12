#!/usr/bin/env node
// Dependency-free A2A v1.0 JSON-RPC loopback agent for the IICP binding proof.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const host = '127.0.0.1';
const extension = 'https://autoagentprotocol.org/extensions/aap/v1.2';

function canonicalDigest(value) {
  const ordered = (input) => {
    if (Array.isArray(input)) return input.map(ordered);
    if (input && typeof input === 'object') {
      return Object.fromEntries(Object.keys(input).sort().map((key) => [key, ordered(input[key])]));
    }
    return input;
  };
  return createHash('sha256').update(JSON.stringify(ordered(value))).digest('hex');
}

function json(response, status, body) {
  const encoded = Buffer.from(JSON.stringify(body));
  response.writeHead(status, {'Content-Type': 'application/json', 'Content-Length': encoded.length});
  response.end(encoded);
}

function collect(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => resolve(Buffer.concat(chunks)));
    request.on('error', reject);
  });
}

const server = createServer(async (request, response) => {
  if (request.method === 'GET' && request.url === '/.well-known/agent-card.json') {
    json(response, 200, server.agentCard);
    return;
  }
  if (request.method !== 'POST' || request.url !== '/a2a') {
    json(response, 404, {error: 'not_found'});
    return;
  }
  if (request.headers.authorization !== 'Bearer a2a-loopback-audience') {
    json(response, 401, {error: 'invalid_a2a_credential'});
    return;
  }
  if (request.headers['x-iicp-dispatch-ticket']) {
    json(response, 400, {error: 'iicp_ticket_passthrough_forbidden'});
    return;
  }
  const body = JSON.parse((await collect(request)).toString('utf8'));
  const part = body?.params?.message?.parts?.[0];
  if (body?.jsonrpc !== '2.0' || body?.method !== 'SendMessage' || part?.data?.type !== 'dealer.information.request') {
    json(response, 200, {jsonrpc: '2.0', id: body?.id ?? null, error: {code: -32602, message: 'Invalid request'}});
    return;
  }
  json(response, 200, {
    jsonrpc: '2.0',
    id: body.id,
    result: {
      message: {
        messageId: 'loopback-response-1',
        role: 'ROLE_AGENT',
        parts: [{
          data: {type: 'dealer.information.response', data: {name: 'IICP Loopback Dealer'}},
          mediaType: 'application/vnd.autoagent.dealer-information-response+json'
        }]
      }
    }
  });
});

server.listen(0, host, () => {
  const {port} = server.address();
  const origin = `http://${host}:${port}`;
  server.agentCard = {
    name: 'IICP AAP loopback agent',
    description: 'Cross-runtime A2A binding proof',
    supportedInterfaces: [{url: `${origin}/a2a`, protocolBinding: 'JSONRPC', protocolVersion: '1.0'}],
    provider: {organization: 'IICP test fixture', url: origin},
    version: '1.0.0',
    capabilities: {streaming: false, extensions: [{uri: extension, description: 'AAP v1.2 typed data', required: true}]},
    securitySchemes: {loopback: {httpAuthSecurityScheme: {scheme: 'bearer'}}},
    securityRequirements: [{schemes: {loopback: {list: []}}}],
    defaultInputModes: ['application/vnd.autoagent.dealer-information-request+json'],
    defaultOutputModes: ['application/vnd.autoagent.dealer-information-response+json'],
    skills: [{id: 'dealer.information', name: 'Dealer information', description: 'Returns public dealer information', tags: ['automotive', 'dealer']}]
  };
  process.stdout.write(`${JSON.stringify({origin, cardUrl: `${origin}/.well-known/agent-card.json`, interfaceUrl: `${origin}/a2a`, cardDigest: canonicalDigest(server.agentCard)})}\n`);
});

for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, () => server.close(() => process.exit(0)));
}

