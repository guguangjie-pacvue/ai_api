
const fs = require('fs');

const adApi = JSON.parse(fs.readFileSync('C:/AI engineering/single-api/ai_api/single-api/endpoints-Amazon.Advertising.Api.json', 'utf8'));
const mainApi = JSON.parse(fs.readFileSync('C:/AI engineering/single-api/ai_api/single-api/endpoints-PacvueMainApi.json', 'utf8'));

const adPaths = new Set(adApi.map(e => e.path));
const mainPaths = new Set(mainApi.map(e => e.path));

const files = [
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/AdGroup/task-2026-08-11-14-07-01/cases.json', swagger: 'Amazon.Advertising.Api', module: 'AdGroup' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/Campaign/task-2026-08-04-18-20-20/cases.json', swagger: 'Amazon.Advertising.Api', module: 'Campaign' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/NegativeTarget/task-2026-08-13T03-07-29/cases.json', swagger: 'Amazon.Advertising.Api', module: 'NegativeTarget' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/Target/task-2026-08-13-11-00-09/cases.json', swagger: 'Amazon.Advertising.Api', module: 'Target' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/Health/task-2026-08-13-14-43-40/cases.json', swagger: 'Amazon.Advertising.Api', module: 'Health' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/KeywordTagAi/task-2026-08-13-14-43-40/cases.json', swagger: 'Amazon.Advertising.Api', module: 'KeywordTagAi' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/ProductAd/task-2026-08-13-14-43-40/cases.json', swagger: 'Amazon.Advertising.Api', module: 'ProductAd' },
  { file: 'C:/AI engineering/single-api/ai_api/single-api/mainapi/PacvueMainApi/Targeting/task-2026-08-13-12-00-55/cases.json', swagger: 'PacvueMainApi', module: 'Targeting' },
];

for (const entry of files) {
  const label = entry.swagger + '/' + entry.module;
  let cases;
  try { cases = JSON.parse(fs.readFileSync(entry.file, 'utf8')); } catch(e) { console.log('[PARSE ERROR] ' + label); continue; }

  for (const c of cases) {
    for (const step of (c.steps || [])) {
      const rawPath = step.path || '';
      const hasLeadingSlash = rawPath.startsWith('/');

      // normalize
      let norm = rawPath.replace(/^\/+/, '');
      if (!norm.startsWith('api/')) norm = 'api/' + norm;
      const apiPath = '/' + norm.split('?')[0];

      const inAd = adPaths.has(apiPath);
      const inMain = mainPaths.has(apiPath);

      if (hasLeadingSlash) {
        console.log('[LEADING_SLASH] ' + label + ' | ' + step.method + ' path=' + rawPath);
      }
      if (!inAd && !inMain) {
        console.log('[NOT_FOUND] ' + label + ' | ' + step.method + ' ' + apiPath);
      } else if (entry.swagger === 'Amazon.Advertising.Api' && !inAd && inMain) {
        console.log('[WRONG_SWAGGER->PacvueMainApi] ' + label + ' | ' + step.method + ' ' + apiPath);
      } else if (entry.swagger === 'PacvueMainApi' && inAd && !inMain) {
        console.log('[WRONG_SWAGGER->AdApi] ' + label + ' | ' + step.method + ' ' + apiPath);
      }

      // Check module tag mismatch (endpoint's first path segment)
      const seg = apiPath.split('/')[2] || '';
      if (seg && seg !== entry.module && !['Health','McpData','SupplementData','EasySqlTest','WeatherForecast'].includes(seg)) {
        console.log('[WRONG_MODULE] ' + label + ' | ' + step.method + ' ' + apiPath + ' (actual module=' + seg + ')');
      }
    }
  }
}
