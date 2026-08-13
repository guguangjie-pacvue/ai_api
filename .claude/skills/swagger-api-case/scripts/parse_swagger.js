/**
 * parse_swagger.js
 * Usage: node scripts/parse_swagger.js <swagger_json_path> [output_json_path]
 *
 * Reads a swagger.json, filters out deprecated endpoints, sorts by tag+path,
 * and writes endpoints-<title>.json (or prints JSON to stdout).
 */
const fs = require('fs');
const path = require('path');

const swaggerPath = process.argv[2];
const outputPath  = process.argv[3]; // optional

if (!swaggerPath) {
  console.error('Usage: node parse_swagger.js <swagger.json> [output.json]');
  process.exit(1);
}

const spec  = JSON.parse(fs.readFileSync(swaggerPath, 'utf8'));
const title = (spec.info && spec.info.title) || 'unknown';
const paths = spec.paths || {};
const rows  = [];

for (const [p, methods] of Object.entries(paths)) {
  for (const [method, op] of Object.entries(methods)) {
    if (!['get','post','put','delete','patch'].includes(method)) continue;
    if (op.deprecated) continue;
    const tag     = (op.tags && op.tags[0]) || '(no tag)';
    const summary = op.summary || '';
    rows.push({ source: title, tag, method: method.toUpperCase(), path: p, summary });
  }
}

rows.sort((a, b) => a.tag.localeCompare(b.tag) || a.path.localeCompare(b.path));

const json = JSON.stringify(rows, null, 2);

if (outputPath) {
  fs.writeFileSync(outputPath, json, 'utf8');
  console.log(`Written ${rows.length} endpoints to ${outputPath}`);
  // Print tag summary
  const counts = {};
  rows.forEach(r => { counts[r.tag] = (counts[r.tag] || 0) + 1; });
  console.log('\n模块 | 接口数');
  Object.entries(counts).sort().forEach(([tag, n]) => console.log(`  ${tag} | ${n}`));
} else {
  process.stdout.write(json);
}
