
const fs = require('fs');

function analyze(file, label) {
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  console.log('\n\n====== ' + label + ' ======');
  for (const [endpoint, bodies] of Object.entries(raw)) {
    console.log('\n--- ' + endpoint + ' (' + bodies.length + ' samples) ---');
    const parsed = [];
    for (const b of bodies) {
      try { parsed.push(typeof b === 'string' ? JSON.parse(b) : b); } catch(e) {}
    }
    if (!parsed.length) { console.log('(no valid bodies)'); continue; }

    // Sample a few to show key fields
    const sample = parsed.slice(0, 5);
    sample.forEach((p, i) => {
      const info = {};
      if (p.ToMarket) info.ToMarket = p.ToMarket;
      if (p.Dim) info.Dim = p.Dim;
      if (p.IsFead !== undefined) info.IsFead = p.IsFead;
      if (p.IsShowNTB !== undefined) info.IsShowNTB = p.IsShowNTB;
      if (p.IsExchange !== undefined) info.IsExchange = p.IsExchange;
      if (p.IsGroupByProfile !== undefined) info.IsGroupByProfile = p.IsGroupByProfile;
      if (p.ProfileIds) info.ProfileIds = '[' + (Array.isArray(p.ProfileIds) ? p.ProfileIds.length + ' ids' : p.ProfileIds) + ']';
      if (p.PageInfo) info.PageSize = p.PageInfo.PageSize;
      if (p.Filters && Array.isArray(p.Filters)) info.Filters = p.Filters.map(f => f.FilterFieldName + '(' + f.FilterType + ')').join(',');
      if (p.asins) info.asins = '[' + p.asins.length + ' asins]';
      if (p.isCheckEdit !== undefined) info.isCheckEdit = p.isCheckEdit;
      if (p.CampaignSTag && p.CampaignSTag.length) info.CampaignSTag = p.CampaignSTag.map(t => t.TagName + (t.TagNameChlid ? '>' + t.TagNameChlid : '')).join(';');
      if (p.AsinSTag && p.AsinSTag.length) info.AsinSTag = p.AsinSTag.map(t => t.TagName + (t.TagNameChlid ? '>' + t.TagNameChlid : '')).join(';');
      console.log('  [' + i + '] ' + JSON.stringify(info));
    });

    // Full dump of first body for case generation
    console.log('\n  FULL_BODY_0: ' + JSON.stringify(parsed[0]));
    if (parsed.length > 1) console.log('  FULL_BODY_1: ' + JSON.stringify(parsed[1]));
    if (parsed.length > 2) console.log('  FULL_BODY_2: ' + JSON.stringify(parsed[2]));
  }
}

analyze(process.env.TEMP + '/es_asintag.json', 'AsinTag');
analyze(process.env.TEMP + '/es_campaigntag.json', 'CampaignTag');
