
const fs = require('fs');
const spec = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_mainapi.json', 'utf8'));
const targets = [
  ['/Health', 'get'],
  ['/api/KeywordTagAi/Match', 'post'],
  ['/api/KeywordTagAi/MatchBySearchTermQuery', 'post'],
  ['/api/KeywordTagAi/MatchBySearchTermQueryV2', 'post'],
  ['/api/KeywordTagAi/MatchByTargetQuery', 'post'],
  ['/api/KeywordTagAi/MatchByTargetQueryV2', 'post'],
  ['/api/KeywordTagAi/MatchV2', 'post'],
  ['/api/ProductAd/GetProductAdChart', 'post'],
  ['/api/ProductAd/GetProductAdPageData', 'post'],
  ['/api/ProductAd/GetProductAdPageDataMaxPageSize', 'post'],
  ['/api/ProductAd/GetProductAdTotal', 'post'],
];

function resolveRef(ref, spec) {
  if (!ref) return null;
  const parts = ref.replace('#/', '').split('/');
  let obj = spec;
  for (const p of parts) obj = obj[p];
  return obj;
}

function flattenSchema(schema, spec, prefix, depth) {
  if (!schema || depth > 4) return [];
  if (schema['$ref']) schema = resolveRef(schema['$ref'], spec);
  if (!schema) return [];
  const rows = [];
  const props = schema.properties || {};
  for (const [k, v] of Object.entries(props)) {
    const path = prefix ? prefix + '.' + k : k;
    let s = v;
    if (s['$ref']) s = resolveRef(s['$ref'], spec) || s;
    const type = s.type || (s['$ref'] ? 'object' : '?');
    const required = (schema.required || []).includes(k);
    const enumVals = s.enum ? s.enum.join('|') : '';
    const example = s.example !== undefined ? s.example : (s.default !== undefined ? s.default : '');
    if (type === 'object' || type === 'array') {
      rows.push({ path, in: 'body', type, required, enum: enumVals, example, desc: s.description || '' });
      const inner = type === 'array' ? s.items : s;
      if (inner) rows.push(...flattenSchema(inner, spec, path + (type==='array'?'[]':''), depth+1));
    } else {
      rows.push({ path, in: 'body', type, required, enum: enumVals, example, desc: s.description || '' });
    }
  }
  return rows;
}

for (const [path, method] of targets) {
  const op = (spec.paths[path] || {})[method];
  if (!op) { console.log(path + ' NOT FOUND'); continue; }
  console.log('\n=== ' + method.toUpperCase() + ' ' + path + ' ===');

  const params = op.parameters || [];
  for (const p of params) {
    const resolved = p['$ref'] ? resolveRef(p['$ref'], spec) : p;
    if (resolved) {
      console.log(JSON.stringify({ path: resolved.name, in: resolved.in, type: resolved.schema?.type || resolved.type || '?', required: resolved.required || false, enum: (resolved.schema?.enum || resolved.enum || []).join('|'), example: resolved.schema?.example ?? resolved.example ?? '', desc: resolved.description || '' }));
    }
  }

  const rb = op.requestBody;
  if (rb) {
    const content = rb.content || {};
    const schema = content['application/json']?.schema || content['*/*']?.schema;
    if (schema) {
      const rows = flattenSchema(schema, spec, '', 0);
      for (const r of rows) console.log(JSON.stringify(r));
    }
  }

  const resp200 = op.responses?.['200'];
  const respContent = resp200?.content?.['application/json']?.schema;
  if (respContent) {
    let s = respContent;
    if (s['$ref']) s = resolveRef(s['$ref'], spec);
    console.log('RESPONSE_KEYS: ' + JSON.stringify(s?.properties ? Object.keys(s.properties) : s?.type));
  }
}
