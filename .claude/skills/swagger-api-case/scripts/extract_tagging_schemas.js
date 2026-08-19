const fs = require('fs');
const swagger = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_mainapi_pacvue.json', 'utf-8'));

const targets = [
  { method: 'get', path: '/api/Tagging/v3/GetAllKeywordTags' },
  { method: 'get', path: '/api/Tagging/v3/GetAllAsinTags' },
  { method: 'get', path: '/api/Tagging/v3/GetAdGroupTag' },
  { method: 'get', path: '/api/Tagging/v3/GetMatchRuleDetail' },
  { method: 'get', path: '/api/Tagging/v3/GetAsinByTag/{tagId}' },
  { method: 'get', path: '/api/Tagging/v3/GetKeywordsByTag' },
  { method: 'get', path: '/api/Tagging/v3/GetAdGroupTagByCampaignMapping' },
  { method: 'post', path: '/api/Tagging/v3/GetCampaignTag' },
  { method: 'post', path: '/api/Tagging/v3/CheckCampaignToTagV2' },
  { method: 'post', path: '/api/Tagging/v3/GetMutilCampaignByCampaignTag' },
  { method: 'post', path: '/api/Tagging/v3/GetAmazonTagNote' },
  { method: 'post', path: '/api/Tagging/v3/CreateTagName' },
  { method: 'post', path: '/api/Tagging/v3/CreateCampaignSubTag' },
  { method: 'post', path: '/api/Tagging/v3/UpdateCampaignTag' },
  { method: 'post', path: '/api/Tagging/v3/UpdateCampaignTagName' },
  { method: 'post', path: '/api/Tagging/v3/CreateAsinTag' },
  { method: 'post', path: '/api/Tagging/v3/EditAsinTag' },
  { method: 'post', path: '/api/Tagging/v3/DeleteAsinTag' },
];

function resolveRef(ref, sw) {
  const parts = ref.replace('#/', '').split('/');
  let cur = sw;
  for (const p of parts) cur = cur[p];
  return cur;
}

function flattenSchema(schema, sw, prefix) {
  prefix = prefix || '';
  if (!schema) return [];
  if (schema['$ref']) schema = resolveRef(schema['$ref'], sw);
  if (schema.type === 'object' || schema.properties) {
    const props = schema.properties || {};
    const req = schema.required || [];
    let rows = [];
    for (const [k, v] of Object.entries(props)) {
      const fk = prefix ? prefix + '.' + k : k;
      let resolved = v['$ref'] ? resolveRef(v['$ref'], sw) : v;
      if (resolved && (resolved.type === 'object' || resolved.properties)) {
        rows = rows.concat(flattenSchema(resolved, sw, fk));
      } else {
        const type = resolved ? (resolved.type || '?') : '?';
        const ev = resolved && resolved.enum ? resolved.enum.join('|') : '';
        const ex = resolved ? (resolved.example !== undefined ? resolved.example : (resolved.default !== undefined ? resolved.default : '')) : '';
        rows.push([fk, type, req.includes(k), ev, ex]);
      }
    }
    return rows;
  } else if (schema.type === 'array') {
    const items = schema.items ? (schema.items['$ref'] ? resolveRef(schema.items['$ref'], sw) : schema.items) : null;
    if (items && (items.type === 'object' || items.properties)) {
      return flattenSchema(items, sw, prefix + '[]');
    }
    return [[prefix + '[]', (items && items.type) || 'any', false, '', '']];
  }
  return [[prefix, schema.type || '?', false, schema.enum ? schema.enum.join('|') : '', schema.example !== undefined ? schema.example : (schema.default !== undefined ? schema.default : '')]];
}

const out = [];
for (const t of targets) {
  const pathObj = swagger.paths[t.path];
  if (!pathObj) { out.push('NOT FOUND: ' + t.path); continue; }
  const op = pathObj[t.method];
  if (!op) { out.push('METHOD NOT FOUND: ' + t.method + ' ' + t.path); continue; }
  out.push('\n=== ' + t.method.toUpperCase() + ' ' + t.path + ' ===');
  if (t.method === 'get' && op.parameters) {
    op.parameters.forEach(p => out.push('  [' + p.in + '] ' + p.name + ' (' + ((p.schema && p.schema.type) || '?') + ') req=' + (p.required || false)));
    if (!op.parameters.length) out.push('  (no params)');
  } else if (t.method === 'get') {
    out.push('  (no params)');
  }
  if (t.method === 'post' && op.requestBody) {
    const content = op.requestBody.content;
    const sc = content && (content['application/json'] || Object.values(content)[0]);
    if (sc && sc.schema) {
      const rows = flattenSchema(sc.schema, swagger);
      rows.forEach(r => out.push('  [body] ' + r[0] + ' (' + r[1] + ') req=' + r[2] + (r[3] ? ' enum:' + r[3] : '') + (r[4] !== '' ? ' ex:' + r[4] : '')));
    }
  }
  const resp200 = op.responses && (op.responses['200'] || op.responses[200]);
  if (resp200 && resp200.content) {
    const sc = resp200.content['application/json'] || Object.values(resp200.content)[0];
    if (sc && sc.schema) {
      let s = sc.schema['$ref'] ? resolveRef(sc.schema['$ref'], swagger) : sc.schema;
      if (s && s.properties && s.properties.data) {
        let ds = s.properties.data['$ref'] ? resolveRef(s.properties.data['$ref'], swagger) : s.properties.data;
        out.push('  Response data type: ' + (ds ? (ds.type || (ds.properties ? 'object' : '?')) : '?'));
        if (ds && ds.properties) {
          Object.keys(ds.properties).slice(0, 5).forEach(k => out.push('    .data.' + k));
        }
      }
    }
  }
}
console.log(out.join('\n'));
