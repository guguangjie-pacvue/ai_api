
/**
 * Fix all structural issues in single-api cases.json files:
 * 1. Leading slash in path field -> remove
 * 2. Campaign cases.json has CampaignPlacement + CampaignTag cases -> split into own dirs
 * 3. NegativeTarget cases.json has PacvueMainApi NegativeTargeting cases -> move to PacvueMainApi/NegativeTargeting
 * 4. Target cases.json has PacvueMainApi Targeting/V3 cases -> move to PacvueMainApi/Targeting, fix base_url
 * 5. PacvueMainApi/Targeting cases have leading slash -> fix
 */

const fs = require('fs');
const path = require('path');

const base = 'C:/AI engineering/single-api/ai_api/single-api/mainapi';

function readJson(f) { return JSON.parse(fs.readFileSync(f, 'utf8')); }
function writeJson(f, data) {
  const dir = path.dirname(f);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(f, JSON.stringify(data, null, 2), 'utf8');
  console.log('WROTE: ' + f);
}

// Fix leading slash in step.path
function fixPath(p) { return p.replace(/^\/+/, ''); }

// Fix all paths in a cases array
function fixPaths(cases) {
  return cases.map(c => ({
    ...c,
    steps: (c.steps || []).map(s => ({ ...s, path: fixPath(s.path || '') }))
  }));
}

// ─── 1. Fix AdGroup leading slashes ───────────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/AdGroup/task-2026-08-11-14-07-01/cases.json';
  const data = fixPaths(readJson(f));
  writeJson(f, data);
}

// ─── 2. Fix Health leading slash ──────────────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/Health/task-2026-08-13-14-43-40/cases.json';
  const data = fixPaths(readJson(f));
  writeJson(f, data);
}

// ─── 3. Fix KeywordTagAi leading slashes ──────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/KeywordTagAi/task-2026-08-13-14-43-40/cases.json';
  const data = fixPaths(readJson(f));
  writeJson(f, data);
}

// ─── 4. Fix ProductAd leading slashes ─────────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/ProductAd/task-2026-08-13-14-43-40/cases.json';
  const data = fixPaths(readJson(f));
  writeJson(f, data);
}

// ─── 5. Split Campaign cases.json ─────────────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/Campaign/task-2026-08-04-18-20-20/cases.json';
  const allCases = readJson(f);

  const campaignCases = [];
  const placementCases = [];
  const tagCases = [];

  for (const c of allCases) {
    const paths = (c.steps || []).map(s => s.path || '');
    const isPlacement = paths.some(p => p.includes('CampaignPlacement'));
    const isTag = paths.some(p => p.includes('CampaignTag'));
    if (isPlacement) placementCases.push(c);
    else if (isTag) tagCases.push(c);
    else campaignCases.push(c);
  }

  // Overwrite Campaign with only Campaign cases
  writeJson(f, campaignCases);

  // Write CampaignPlacement to its own dir (same task timestamp)
  writeJson(
    base + '/Amazon.Advertising.Api/CampaignPlacement/task-2026-08-04-18-20-20/cases.json',
    fixPaths(placementCases)
  );

  // CampaignTag already has better cases in task-2026-08-13-14-30-00
  // Write old tag cases to a separate timestamped dir so nothing is lost
  if (tagCases.length > 0) {
    writeJson(
      base + '/Amazon.Advertising.Api/CampaignTag/task-2026-08-04-18-20-20/cases.json',
      fixPaths(tagCases)
    );
    console.log('NOTE: Old CampaignTag cases from Campaign moved to CampaignTag/task-2026-08-04-18-20-20 (superseded by task-2026-08-13-14-30-00)');
  }

  console.log('Campaign split: Campaign=' + campaignCases.length + ' Placement=' + placementCases.length + ' Tag=' + tagCases.length);
}

// ─── 6. Split NegativeTarget cases.json ───────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/NegativeTarget/task-2026-08-13T03-07-29/cases.json';
  const allCases = readJson(f);

  const negTargetCases = [];   // Amazon.Advertising.Api NegativeTarget
  const negTargetingCases = []; // PacvueMainApi NegativeTargeting

  for (const c of allCases) {
    const paths = (c.steps || []).map(s => s.path || '');
    const isPacvue = paths.some(p => p.toLowerCase().includes('negativetargeting'));
    if (isPacvue) negTargetingCases.push(c);
    else negTargetCases.push(c);
  }

  // Fix leading slash and overwrite NegativeTarget
  writeJson(f, fixPaths(negTargetCases));

  // Move NegativeTargeting cases to PacvueMainApi, fix base_url to BASEURL
  if (negTargetingCases.length > 0) {
    const fixed = fixPaths(negTargetingCases).map(c => ({
      ...c,
      steps: (c.steps || []).map(s => ({
        ...s,
        base_url: s.base_url === '{{INDBASEURL}}' ? '{{BASEURL}}' : s.base_url
      }))
    }));
    writeJson(
      base + '/PacvueMainApi/NegativeTargeting/task-2026-08-13T03-07-29/cases.json',
      fixed
    );
  }

  console.log('NegativeTarget split: AdApi=' + negTargetCases.length + ' PacvueMain=' + negTargetingCases.length);
}

// ─── 7. Split Target cases.json ───────────────────────────────────────────────
{
  const f = base + '/Amazon.Advertising.Api/Target/task-2026-08-13-11-00-09/cases.json';
  const allCases = readJson(f);

  const targetCases = [];    // Amazon.Advertising.Api Target
  const targetingCases = []; // PacvueMainApi Targeting V3

  for (const c of allCases) {
    const paths = (c.steps || []).map(s => s.path || '');
    // Targeting/V3 paths belong to PacvueMainApi
    const isPacvue = paths.some(p => /^\/?(Targeting\/V3)/i.test(p));
    if (isPacvue) targetingCases.push(c);
    else targetCases.push(c);
  }

  writeJson(f, fixPaths(targetCases));

  // PacvueMainApi Targeting already has task-2026-08-13-12-00-55
  // Move old Targeting cases to a separate timestamp to avoid overwriting
  if (targetingCases.length > 0) {
    const fixed = fixPaths(targetingCases).map(c => ({
      ...c,
      steps: (c.steps || []).map(s => ({
        ...s,
        base_url: s.base_url === '{{INDBASEURL}}' ? '{{BASEURL}}' : s.base_url
      }))
    }));
    writeJson(
      base + '/PacvueMainApi/Targeting/task-2026-08-13-11-00-09/cases.json',
      fixed
    );
  }

  console.log('Target split: AdApi=' + targetCases.length + ' PacvueMain=' + targetingCases.length);
}

// ─── 8. Fix PacvueMainApi/Targeting leading slashes ──────────────────────────
{
  const f = base + '/PacvueMainApi/Targeting/task-2026-08-13-12-00-55/cases.json';
  const data = fixPaths(readJson(f));
  writeJson(f, data);
}

console.log('\nAll fixes applied.');
