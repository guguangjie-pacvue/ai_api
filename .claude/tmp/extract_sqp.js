const fs = require('fs');
const swagger = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_mainapi.json', 'utf8'));

const sqpPaths = Object.keys(swagger.paths).filter(p => p.includes('SQPAnalysis'));
console.log('SQPAnalysis paths found:', sqpPaths.length);

function resolveRef(ref) {
  const parts = ref.replace('#/', '').split('/');
  let obj = swagger;
  for (const part of parts) obj = obj[part];
  return obj;
}

function extractFields(schema, prefix, required) {
  if (schema['$ref']) schema = resolveRef(schema['$ref']);
  if (!schema.properties) return;
  Object.entries(schema.properties).forEach(([k, v]) => {
    const fullKey = prefix ? prefix + '.' + k : k;
    const isReq = (required||[]).includes(k) ? 'Y' : 'N';
    if (v['$ref']) {
      const resolved = resolveRef(v['$ref']);
      if (resolved.properties) {
        extractFields(resolved, fullKey, resolved.required);
      } else {
        console.log(fullKey + ' | body | ' + (resolved.type||'object') + ' | ' + isReq + ' | ' + JSON.stringify(v.example||resolved.example||''));
      }
    } else if (v.type === 'array' && v.items) {
      if (v.items['$ref']) {
        const resolved = resolveRef(v.items['$ref']);
        console.log(fullKey + '[] | body | array | ' + isReq + ' | [' + v.items['$ref'].split('/').pop() + ']');
      } else {
        console.log(fullKey + ' | body | array | ' + isReq + ' | ' + JSON.stringify(v.example||''));
      }
    } else {
      console.log(fullKey + ' | body | ' + (v.type||'object') + ' | ' + isReq + ' | example:' + JSON.stringify(v.example||v.default||'') + ' | enum:' + JSON.stringify(v.enum||''));
    }
  });
}

sqpPaths.forEach(p => {
  const methods = Object.keys(swagger.paths[p]);
  methods.forEach(m => {
    const op = swagger.paths[p][m];
    console.log('\n=== ' + m.toUpperCase() + ' ' + p + ' ===');
    if (op.requestBody) {
      const content = op.requestBody.content;
      const mediaType = Object.keys(content)[0];
      const schema = content[mediaType].schema;
      extractFields(schema, '', schema.required);
    } else {
      console.log('  (no requestBody)');
    }
  });
});
