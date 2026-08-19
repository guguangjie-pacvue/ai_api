const fs = require('fs');
const sw = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_mainapi_pacvue.json', 'utf-8'));

function resolveRef(ref, sw) {
  const parts = ref.replace('#/', '').split('/');
  let cur = sw;
  for (const p of parts) cur = cur[p];
  return cur;
}

function flatSchema(schema, sw, prefix) {
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
        rows = rows.concat(flatSchema(resolved, sw, fk));
      } else {
        const type = resolved ? (resolved.type || '?') : '?';
        rows.push(fk + ' (' + type + ')');
      }
    }
    return rows;
  } else if (schema.type === 'array') {
    const items = schema.items ? (schema.items['$ref'] ? resolveRef(schema.items['$ref'], sw) : schema.items) : null;
    if (items && (items.type === 'object' || items.properties)) return flatSchema(items, sw, prefix + '[]');
    return [prefix + '[] (' + ((items && items.type) || 'any') + ')'];
  }
  return [prefix + ' (' + (schema.type || '?') + ')'];
}

const checks = [
  { path: '/api/Tagging/v3/BulkDeleteCampaignTag', method: 'post' },
  { path: '/api/Tagging/v3/CreateTagName', method: 'post' },
  { path: '/api/Tagging/v3/GetCampaignByCampaignTag', method: 'post' },
  { path: '/api/Tagging/v3/DeleteAdGroupFromTag', method: 'post' },
  { path: '/api/Tagging/v3/AddAdGroupsToTags', method: 'post' },
];

for (const t of checks) {
  const pathObj = sw.paths[t.path];
  if (!pathObj) { console.log('NOT FOUND: ' + t.path); continue; }
  const op = pathObj[t.method];
  if (!op) { console.log('METHOD NOT FOUND: ' + t.method + ' ' + t.path); continue; }
  console.log('\n=== ' + t.method.toUpperCase() + ' ' + t.path + ' ===');
  if (op.requestBody && op.requestBody.content) {
    const sc = op.requestBody.content['application/json'] || Object.values(op.requestBody.content)[0];
    if (sc && sc.schema) {
      flatSchema(sc.schema, sw).forEach(function(r) { console.log('  REQ: ' + r); });
    }
  }
  const resp200 = op.responses && (op.responses['200'] || op.responses[200]);
  if (resp200 && resp200.content) {
    const sc = resp200.content['application/json'] || Object.values(resp200.content)[0];
    if (sc && sc.schema) {
      let s = sc.schema['$ref'] ? resolveRef(sc.schema['$ref'], sw) : sc.schema;
      if (s && s.properties && s.properties.data) {
        let ds = s.properties.data['$ref'] ? resolveRef(s.properties.data['$ref'], sw) : s.properties.data;
        flatSchema(ds, sw, 'data').forEach(function(r) { console.log('  RESP: ' + r); });
      } else {
        console.log('  RESP data: no data field in response');
      }
    }
  }
}
