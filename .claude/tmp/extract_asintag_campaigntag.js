
const fs = require('fs');
const spec = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_mainapi.json', 'utf8'));
const defs = spec.definitions || (spec.components && spec.components.schemas) || {};
const paths = spec.paths || {};

function resolveRef(ref) {
  if (!ref) return null;
  const name = ref.replace('#/definitions/', '').replace('#/components/schemas/', '');
  return defs[name] || null;
}

function flattenSchema(schema, prefix, depth) {
  if (!schema || depth > 4) return [];
  if (schema.$ref) schema = resolveRef(schema.$ref) || schema;
  const rows = [];
  if (schema.type === 'object' || schema.properties) {
    const props = schema.properties || {};
    const reqList = schema.required || [];
    for (const [k, v] of Object.entries(props)) {
      let s = v;
      if (s.$ref) s = resolveRef(s.$ref) || s;
      const fullKey = prefix ? prefix + '.' + k : k;
      const required = reqList.includes(k) ? 'Y' : 'N';
      let type = s.type || (s.$ref ? 'object' : 'unknown');
      if (s.items) {
        const iref = s.items.$ref ? s.items.$ref.split('/').pop() : (s.items.type || 'any');
        type = 'array<' + iref + '>';
      }
      const enumVals = (s.enum || []).join(',');
      const example = s.example !== undefined ? s.example : (s.default !== undefined ? s.default : '');
      rows.push({ field: fullKey, type, required, enum: enumVals, example: String(example), desc: s.description || '' });
      if ((s.type === 'object' || s.properties) && depth < 3) {
        rows.push(...flattenSchema(s, fullKey, depth + 1));
      } else if (s.type === 'array' && s.items) {
        let itemSchema = s.items;
        if (itemSchema.$ref) itemSchema = resolveRef(itemSchema.$ref) || itemSchema;
        if (itemSchema.properties) rows.push(...flattenSchema(itemSchema, fullKey + '[]', depth + 1));
      }
    }
  }
  return rows;
}

const tags = ['AsinTag', 'CampaignTag'];
for (const [path, methods] of Object.entries(paths)) {
  for (const [method, op] of Object.entries(methods)) {
    if (!['get','post','put','delete','patch'].includes(method) || op.deprecated) continue;
    const tag = (op.tags && op.tags[0]) || '';
    if (!tags.includes(tag)) continue;

    console.log('\n========== ' + method.toUpperCase() + ' ' + path + ' ==========');
    console.log('TAG:' + tag);
    console.log('SUMMARY:' + (op.summary || ''));

    if (op.parameters && op.parameters.length) {
      op.parameters.forEach(p => {
        const s = p.schema || p;
        const ex = s.example !== undefined ? s.example : (s.default !== undefined ? s.default : '');
        console.log('PARAM|' + p.name + '|' + (p.in || 'query') + '|' + (s.type || '') + '|' + (p.required ? 'Y' : 'N') + '|' + (s.enum || []).join(',') + '|' + ex + '|' + (p.description || ''));
      });
    }

    const body = op.requestBody;
    if (body) {
      const content = body.content || {};
      const jsonContent = content['application/json'] || Object.values(content)[0];
      if (jsonContent && jsonContent.schema) {
        let schema = jsonContent.schema;
        if (schema.$ref) schema = resolveRef(schema.$ref) || schema;
        const rows = flattenSchema(schema, '', 0);
        rows.forEach(r => console.log('BODY|' + r.field + '|' + r.type + '|' + r.required + '|' + r.enum + '|' + r.example + '|' + r.desc));
      }
    }

    const resp200 = op.responses && op.responses['200'];
    if (resp200) {
      const content = resp200.content || {};
      const jsonContent = content['application/json'] || Object.values(content)[0];
      if (jsonContent && jsonContent.schema) {
        let schema = jsonContent.schema;
        if (schema.$ref) schema = resolveRef(schema.$ref) || schema;
        const rows = flattenSchema(schema, '', 0);
        rows.slice(0, 15).forEach(r => console.log('RESP|' + r.field + '|' + r.type));
      }
    }
  }
}
