import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webConsoleRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(webConsoleRoot, '..', '..');
const outputPath = path.resolve(webConsoleRoot, 'src/generated/control-api-sdk/index.ts');

const openapiJson = execFileSync(
  'python',
  [
    '-c',
    [
      'import json',
      'import sys',
      'sys.path.insert(0, "apps/control-api")',
      'from app.main import app',
      'print(json.dumps(app.openapi()))',
    ].join('; '),
  ],
  {
    cwd: repoRoot,
    encoding: 'utf8',
  },
);

const schema = JSON.parse(openapiJson);

function refName(ref) {
  return ref.split('/').pop();
}

function toTsType(node) {
  if (!node) {
    return 'unknown';
  }
  if (node.$ref) {
    return refName(node.$ref);
  }
  if (node.allOf) {
    return [...new Set(node.allOf.map(toTsType))].join(' & ');
  }
  if (node.anyOf) {
    return [...new Set(node.anyOf.map(toTsType))].join(' | ');
  }
  if (node.oneOf) {
    return [...new Set(node.oneOf.map(toTsType))].join(' | ');
  }

  let resolved;
  if (node.enum) {
    resolved = node.enum.map((value) => JSON.stringify(value)).join(' | ');
  } else if (node.type === 'null') {
    resolved = 'null';
  } else if (node.type === 'string') {
    resolved = 'string';
  } else if (node.type === 'integer' || node.type === 'number') {
    resolved = 'number';
  } else if (node.type === 'boolean') {
    resolved = 'boolean';
  } else if (node.type === 'array') {
    resolved = `${wrapType(toTsType(node.items))}[]`;
  } else if (node.type === 'object' || node.properties || node.additionalProperties) {
    if (node.properties) {
      const required = new Set(node.required ?? []);
      const members = Object.entries(node.properties).map(([key, value]) => {
        const optional = required.has(key) ? '' : '?';
        return `${JSON.stringify(key)}${optional}: ${toTsType(value)};`;
      });
      if (node.additionalProperties) {
        members.push(`[key: string]: ${toTsType(node.additionalProperties)};`);
      }
      resolved = `{ ${members.join(' ')} }`;
    } else if (node.additionalProperties) {
      resolved = `Record<string, ${toTsType(node.additionalProperties)}>`;
    } else {
      resolved = 'Record<string, unknown>';
    }
  } else {
    resolved = 'unknown';
  }

  if (node.nullable) {
    return `${resolved} | null`;
  }
  return resolved;
}

function wrapType(typeName) {
  return typeName.includes(' | ') ? `(${typeName})` : typeName;
}

function emitSchema(name, node) {
  if ((node.type === 'object' || node.properties) && node.properties) {
    const required = new Set(node.required ?? []);
    const members = Object.entries(node.properties)
      .map(([key, value]) => {
        const optional = required.has(key) ? '' : '?';
        return `  ${JSON.stringify(key)}${optional}: ${toTsType(value)};`;
      })
      .join('\n');
    return `export interface ${name} {\n${members}\n}`;
  }
  return `export type ${name} = ${toTsType(node)};`;
}

function firstJsonResponse(operation) {
  for (const [statusCode, response] of Object.entries(operation.responses ?? {})) {
    if (!statusCode.startsWith('2')) {
      continue;
    }
    const content = response.content ?? {};
    if (content['application/json']?.schema) {
      return content['application/json'].schema;
    }
  }
  return null;
}

function requestBodySchema(operation) {
  const content = operation.requestBody?.content ?? {};
  return content['application/json']?.schema ?? null;
}

const operationsById = new Map();
for (const [routePath, methods] of Object.entries(schema.paths ?? {})) {
  for (const [method, operation] of Object.entries(methods)) {
    operationsById.set(operation.operationId, {
      method: method.toUpperCase(),
      path: routePath,
      operation,
    });
  }
}

const mappedOperations = {
  proceduresApi: {
    start: 'operator_start_procedure',
    list: 'operator_list_procedures',
    getStatus: 'operator_get_procedure_status',
  },
  tenantsApi: {
    list: 'operator_list_tenants',
    get: 'operator_get_tenant',
  },
  publicProceduresApi: {
    start: 'public_start_procedure',
    getStatus: 'public_get_procedure_status',
  },
  streamsApi: {
    issueTicket: 'issue_stream_ticket',
  },
};

function responseTypeFor(operationId) {
  const entry = operationsById.get(operationId);
  const responseSchema = firstJsonResponse(entry.operation);
  return responseSchema ? toTsType(responseSchema) : 'unknown';
}

function requestTypeFor(operationId) {
  const entry = operationsById.get(operationId);
  const bodySchema = requestBodySchema(entry.operation);
  return bodySchema ? toTsType(bodySchema) : null;
}

const components = Object.entries(schema.components?.schemas ?? {})
  .map(([name, node]) => emitSchema(name, node))
  .join('\n\n');

const lines = [
  '// This file is generated from apps/control-api OpenAPI. Do not edit manually.',
  '',
  "import { apiFetch } from '../../shared/api';",
  '',
  components,
  '',
  'export type ProcedureHandle = ProcedureHandleDTO;',
  'export type ProcedureStatus = ProcedureStatusDTO;',
  'export type Tenant = TenantSummary;',
  '',
  'function withQuery(path: string, params?: Record<string, string | number | undefined>): string {',
  '  const search = new URLSearchParams();',
  '  for (const [key, value] of Object.entries(params ?? {})) {',
  '    if (value !== undefined) {',
  '      search.set(key, String(value));',
  '    }',
  '  }',
  "  const query = search.toString();",
  '  return query ? `${path}?${query}` : path;',
  '}',
  '',
  `export const proceduresApi = {`,
  `  start: (body: ${requestTypeFor(mappedOperations.proceduresApi.start)}): Promise<${responseTypeFor(mappedOperations.proceduresApi.start)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.proceduresApi.start).path}', { method: '${operationsById.get(mappedOperations.proceduresApi.start).method}', body }),`,
  `  list: (tenantId: string, params?: { status?: string; limit?: number; offset?: number }): Promise<${responseTypeFor(mappedOperations.proceduresApi.list)}> =>`,
  `    apiFetch(withQuery('${operationsById.get(mappedOperations.proceduresApi.list).path}', { tenant_id: tenantId, ...params })),`,
  `  getStatus: (workflowId: string): Promise<${responseTypeFor(mappedOperations.proceduresApi.getStatus)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.proceduresApi.getStatus).path}'.replace('{workflow_id}', encodeURIComponent(workflowId))),`,
  `};`,
  '',
  `export const tenantsApi = {`,
  `  list: (params?: { limit?: number; offset?: number }): Promise<${responseTypeFor(mappedOperations.tenantsApi.list)}> =>`,
  `    apiFetch(withQuery('${operationsById.get(mappedOperations.tenantsApi.list).path}', params)),`,
  `  get: (tenantId: string): Promise<${responseTypeFor(mappedOperations.tenantsApi.get)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.tenantsApi.get).path}'.replace('{tenant_id}', encodeURIComponent(tenantId))),`,
  `};`,
  '',
  `export const publicProceduresApi = {`,
  `  start: (body: ${requestTypeFor(mappedOperations.publicProceduresApi.start)}): Promise<${responseTypeFor(mappedOperations.publicProceduresApi.start)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.publicProceduresApi.start).path}', { method: '${operationsById.get(mappedOperations.publicProceduresApi.start).method}', body }),`,
  `  getStatus: (workflowId: string): Promise<${responseTypeFor(mappedOperations.publicProceduresApi.getStatus)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.publicProceduresApi.getStatus).path}'.replace('{workflow_id}', encodeURIComponent(workflowId))),`,
  `};`,
  '',
  `export const streamsApi = {`,
  `  issueTicket: (): Promise<${responseTypeFor(mappedOperations.streamsApi.issueTicket)}> =>`,
  `    apiFetch('${operationsById.get(mappedOperations.streamsApi.issueTicket).path}', { method: '${operationsById.get(mappedOperations.streamsApi.issueTicket).method}' }),`,
  `};`,
  '',
];

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${lines.join('\n')}\n`);
