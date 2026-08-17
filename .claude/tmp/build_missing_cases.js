const fs = require('fs');
const casesPath = 'C:/AI engineering/single-api/ai_api/single-api/mainapi/Amazon.Advertising.Api/AdGroup/task-2026-08-11-14-07-01/cases.json';
const tmpDir = 'C:/Users/ShaoboZhang/AppData/Local/Temp';

const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));

function transformBody(b) {
  const rb = JSON.parse(JSON.stringify(b));
  if (Array.isArray(rb.ProfileIds)) rb.ProfileIds = ['{{profile_id}}'];
  (rb.Filters || []).forEach(f => {
    const fn = f.filterFieldName;
    if (typeof f.filterContent !== 'string') return;
    if (fn === 'ReportDateTime') {
      try {
        const parsed = JSON.parse(f.filterContent);
        if (parsed.FilterBetween) {
          parsed.FilterBetween.start = '{{date_start_mdy}}';
          parsed.FilterBetween.end = '{{date_end_mdy}}';
          f.filterContent = JSON.stringify(parsed);
        }
      } catch(e) {}
    } else if (fn === 'CampaignId') {
      f.filterContent = '["{{campaign_id}}"]';
    } else if (fn === 'AdGroupId') {
      f.filterContent = '["{{adgroup_id}}"]';
    }
  });
  return rb;
}

function makeCase(apiName, sceneName, sceneDesc, rb, assertion) {
  return {
    name: `POST /api/AdGroup/${apiName} - ${sceneName}`,
    description: `单接口测试：POST /api/AdGroup/${apiName}。${sceneDesc}。`,
    module: 'AdGroup', granularity: 'API', since: 'init', last_modified: 'init',
    change_type: 'NEW', generated_by: 'swagger-api-case',
    steps: [{
      name: `调用 ${apiName}`, method: 'POST', base_url: '{{INDBASEURL}}',
      path: `AdGroup/${apiName}`, request_body: transformBody(rb),
      extract_vars: {}, expected_response: assertion
    }]
  };
}

const CHART_ASSERT = { code: 200, success: true, data: { '$is_array': true } };
const PAGE_ASSERT  = { code: 200, success: true, data: { pageInfo: { '$not_empty': true } } };
const TOTAL_ASSERT = { code: 200, success: true, data: { '$not_empty': true } };

function load(prefix, label) {
  let content = fs.readFileSync(`${tmpDir}/${prefix}_${label}.json`, 'utf8');
  if (content.charCodeAt(0) === 0xFEFF) content = content.slice(1); // strip BOM
  return JSON.parse(content);
}

const chartNew = [
  makeCase('GetAdGroupChart', '场景4_AdGroupName搜索_ytd_US',   '按AdGroupName关键字搜索广告组，ytd维度',             load('chart','场景4_AdGroupName搜索'),        CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景5_JP市场_Campaign下钻_ytd',   '日本市场Campaign下钻查看广告组，ytd维度',            load('chart','场景5_JP_Campaign下钻'),         CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景6_AU市场_Campaign下钻_ytd',   '澳大利亚市场Campaign下钻查看广告组，ytd维度',        load('chart','场景6_AU_Campaign下钻'),         CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景7_CampaignTagId筛选_ytd_US',  '按Campaign标签筛选广告组，ytd维度',                  load('chart','场景7_CampaignTagId筛选'),       CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景8_CampaignName搜索_ytd_US',   '按CampaignName关键字搜索，ytd维度',                  load('chart','场景8_CampaignName搜索'),        CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景9_AdGroupId+CampaignId下钻_ytd_US', 'AdGroupId+CampaignId双重精确下钻，ytd维度', load('chart','场景9_AdGroupId+CampaignId下钻'),CHART_ASSERT),
  makeCase('GetAdGroupChart', '场景10_AdGroupId精确_ytd_US',     '按AdGroupId精确查看，ytd维度',                       load('chart','场景10_AdGroupId精确'),         CHART_ASSERT),
];

const pageNew = [
  makeCase('GetAdGroupPageData', '场景6_自定义日期范围_Dim1_跨profile',   '自定义日期区间(Dim=1)，跨多profile浏览广告组列表',  load('page','场景6_Dim1_默认'),           PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景7_CampaignTagId筛选_ytd_US',        '按Campaign标签筛选广告组分页列表，ytd维度',         load('page','场景7_CampaignTagId'),       PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景8_AdGroupName搜索_ytd_US',           '按AdGroupName关键字搜索，ytd维度',                  load('page','场景8_AdGroupName搜索'),     PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景9_AdGroupId+CampaignId双重精确_ytd', 'AdGroupId+CampaignId双重精确下钻分页，ytd维度',    load('page','场景9_AdGroupId+CampaignId'),PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景10_JP市场_Campaign下钻_ytd',         '日本市场Campaign下钻广告组分页，ytd维度',           load('page','场景10_JP_Campaign下钻'),    PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景11_JP市场_CampaignName搜索_ytd',     '日本市场按CampaignName搜索广告组，ytd维度',         load('page','场景11_JP_CampaignName'),    PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景12_CampaignName搜索_ytd_US',         '按CampaignName关键字搜索广告组分页，ytd维度',       load('page','场景12_CampaignName搜索'),   PAGE_ASSERT),
  makeCase('GetAdGroupPageData', '场景13_AdGroupName+CampaignTagId复合_ytd','AdGroupName搜索+CampaignTagId标签复合筛选，ytd维度',load('page','场景13_AdGroupName+CampaignTagId'),PAGE_ASSERT),
];

const totalNew = [
  makeCase('GetAdGroupTotal', '场景1_默认列表浏览_ytd_US',              '默认列表浏览，ytd维度无特殊筛选，State过滤',         load('total','场景1_默认浏览'),           TOTAL_ASSERT),
  makeCase('GetAdGroupTotal', '场景6_AdGroupId+CampaignId双重精确_ytd', 'AdGroupId+CampaignId双重精确定位汇总数据',           load('total','场景6_AdGroupId+CampaignId'),TOTAL_ASSERT),
  makeCase('GetAdGroupTotal', '场景7_CampaignTagId筛选_ytd_US',         '按Campaign标签筛选汇总，ytd维度',                    load('total','场景7_CampaignTagId'),      TOTAL_ASSERT),
  makeCase('GetAdGroupTotal', '场景8_AdGroupName+CampaignTagId复合_ytd','AdGroupName搜索+CampaignTagId标签复合筛选汇总',      load('total','场景8_AdGroupName+CampaignTagId'),TOTAL_ASSERT),
];

const page  = cases.filter(c => c.steps[0].path.includes('GetAdGroupPageData'));
const total = cases.filter(c => c.steps[0].path.includes('GetAdGroupTotal'));
const chart = cases.filter(c => c.steps[0].path.includes('GetAdGroupChart'));

const finalCases = [...page, ...pageNew, ...total, ...totalNew, ...chart, ...chartNew];

fs.writeFileSync(casesPath, JSON.stringify(finalCases, null, 2), 'utf8');

console.log('Total cases:', finalCases.length);
['GetAdGroupPageData','GetAdGroupTotal','GetAdGroupChart'].forEach(api => {
  const n = finalCases.filter(c => c.steps[0].path.includes(api)).length;
  console.log(`  ${api}: ${n}`);
});
