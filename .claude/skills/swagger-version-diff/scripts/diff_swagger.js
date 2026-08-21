/**
 * diff_swagger.js
 * 比较两个 Swagger JSON，输出接口级变更：added / removed / modified
 *
 * 用法：
 *   node diff_swagger.js <baseline.json> <target.json> <output_diff.json>
 *
 * 输出格式：
 * {
 *   "summary": { "added": N, "removed": N, "modified": N, "unchanged": N },
 *   "added":    [{ "method", "path", "tag", "summary" }],
 *   "removed":  [{ "method", "path", "tag", "summary" }],
 *   "modified": [{ "method", "path", "tag", "summary", "changes": [...] }],
 *   "unchanged": [{ "method", "path" }]
 * }
 */

const fs = require('fs');

const [, , baselinePath, targetPath, outputPath] = process.argv;
if (!baselinePath || !targetPath || !outputPath) {
  console.error('Usage: node diff_swagger.js <baseline.json> <target.json> <output_diff.json>');
  process.exit(1);
}

const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
const target   = JSON.parse(fs.readFileSync(targetPath,   'utf8'));

function extractEndpoints(spec) {
  const paths = spec.paths || {};
  const result = {};
  for (const [path, pathItem] of Object.entries(paths)) {
    for (const method of ['get','post','put','patch','delete','options','head']) {
      const op = pathItem[method];
      if (!op || op.deprecated) continue;
      const key = `${method.toUpperCase()} ${path}`;
      result[key] = { method: method.toUpperCase(), path, op };
    }
  }
  return result;
}

function resolveRef(spec, obj, visited = new Set()) {
  if (!obj || typeof obj !== 'object') return obj;
  if (obj.$ref) {
    if (visited.has(obj.$ref)) return { type: 'circular' };
    const parts = obj.$ref.replace(/^#\//, '').split('/');
    let cur = spec;
    for (const p of parts) cur = cur?.[p];
    return resolveRef(spec, cur, new Set([...visited, obj.$ref]));
  }
  const out = Array.isArray(obj) ? [] : {};
  for (const [k, v] of Object.entries(obj)) {
    out[k] = resolveRef(spec, v, visited);
  }
  return out;
}

function extractParams(spec, op) {
  const params = (op.parameters || []).map(p => {
    const r = resolveRef(spec, p);
    return { name: r.name, in: r.in, required: !!r.required, type: r.schema?.type || r.type || '?' };
  });

  let bodyFields = [];
  if (op.requestBody) {
    const rb = resolveRef(spec, op.requestBody);
    const content = rb.content || {};
    const jsonContent = content['application/json'] || Object.values(content)[0];
    if (jsonContent?.schema) {
      bodyFields = flattenSchema(spec, jsonContent.schema, '');
    }
  }
  return { params, bodyFields };
}

function flattenSchema(spec, schema, prefix, visited = new Set()) {
  const resolved = resolveRef(spec, schema, visited);
  if (!resolved || typeof resolved !== 'object') return [];

  const type = resolved.type;
  if (type === 'object' || resolved.properties) {
    const props = resolved.properties || {};
    const required = resolved.required || [];
    const result = [];
    for (const [key, val] of Object.entries(props)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const sub = flattenSchema(spec, val, fullKey, visited);
      if (sub.length) {
        result.push(...sub);
      } else {
        const r = resolveRef(spec, val, visited);
        result.push({ field: fullKey, type: r?.type || '?', required: required.includes(key) });
      }
    }
    return result;
  }
  if (type === 'array' && resolved.items) {
    return flattenSchema(spec, resolved.items, prefix ? `${prefix}[]` : '[]', visited);
  }
  if (prefix) {
    return [{ field: prefix, type: type || '?', required: false }];
  }
  return [];
}

function toMap(fields) {
  const m = {};
  for (const f of fields) m[f.field] = f;
  return m;
}

const baseEndpoints = extractEndpoints(baseline);
const targEndpoints = extractEndpoints(target);
const baseKeys = new Set(Object.keys(baseEndpoints));
const targKeys = new Set(Object.keys(targEndpoints));

const added = [], removed = [], modified = [], unchanged = [];

for (const key of targKeys) {
  if (!baseKeys.has(key)) {
    const { method, path, op } = targEndpoints[key];
    added.push({ method, path, tag: (op.tags || [])[0] || '', summary: op.summary || '' });
  }
}

for (const key of baseKeys) {
  if (!targKeys.has(key)) {
    const { method, path, op } = baseEndpoints[key];
    removed.push({ method, path, tag: (op.tags || [])[0] || '', summary: op.summary || '' });
  }
}

for (const key of baseKeys) {
  if (!targKeys.has(key)) continue;
  const { method, path, op: baseOp } = baseEndpoints[key];
  const { op: targOp } = targEndpoints[key];
  const tag = (targOp.tags || [])[0] || '';
  const summary = targOp.summary || '';
  const changes = [];

  const baseP = extractParams(baseline, baseOp);
  const targP = extractParams(target,   targOp);

  const bPMap = {};
  for (const p of baseP.params) bPMap[`${p.in}:${p.name}`] = p;
  const tPMap = {};
  for (const p of targP.params) tPMap[`${p.in}:${p.name}`] = p;

  for (const k of Object.keys(tPMap)) {
    if (!bPMap[k]) {
      changes.push({ type: 'param_added', detail: k });
    } else {
      const b = bPMap[k], t = tPMap[k];
      if (b.required !== t.required)
        changes.push({ type: 'param_required_changed', detail: `${k}: required ${b.required}→${t.required}` });
      if (b.type !== t.type)
        changes.push({ type: 'param_type_changed', detail: `${k}: type ${b.type}→${t.type}` });
    }
  }
  for (const k of Object.keys(bPMap)) {
    if (!tPMap[k]) changes.push({ type: 'param_removed', detail: k });
  }

  const bBMap = toMap(baseP.bodyFields);
  const tBMap = toMap(targP.bodyFields);
  for (const f of Object.keys(tBMap)) {
    if (!bBMap[f]) {
      changes.push({ type: 'body_field_added', detail: f });
    } else {
      if (bBMap[f].type !== tBMap[f].type)
        changes.push({ type: 'body_field_type_changed', detail: `${f}: ${bBMap[f].type}→${tBMap[f].type}` });
      if (bBMap[f].required !== tBMap[f].required)
        changes.push({ type: 'body_field_required_changed', detail: `${f}: required ${bBMap[f].required}→${tBMap[f].required}` });
    }
  }
  for (const f of Object.keys(bBMap)) {
    if (!tBMap[f]) changes.push({ type: 'body_field_removed', detail: f });
  }

  if (changes.length > 0) {
    modified.push({ method, path, tag, summary, changes });
  } else {
    unchanged.push({ method, path });
  }
}

const diff = {
  summary: { added: added.length, removed: removed.length, modified: modified.length, unchanged: unchanged.length },
  added, removed, modified, unchanged,
};

fs.writeFileSync(outputPath, JSON.stringify(diff, null, 2), 'utf8');
console.log(`Diff: +${diff.summary.added} added, -${diff.summary.removed} removed, ~${diff.summary.modified} modified, =${diff.summary.unchanged} unchanged`);
console.log(`Output: ${outputPath}`);
