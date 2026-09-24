# target-api 近90天 ES 无流量接口清单

- 索引：`target-access-*`　窗口：近90天　生成：2026-09-24
- 总接口 **648**　无流量 **307**　有流量 **341**　查询失败 0
- 匹配口径：urlReferrer.keyword **精确匹配**（大小写/`/api`前缀敏感），模板路径 `{param}` 按 `[^/]+` 正则匹配真实 ID；与 criteo 同法

## 一、整模块 100% 无流量（模块内所有接口近90天 0 调用）

| 模块(Tag) | 接口数 |
|---|---|
| my-report-controller | 25 |
| 1-Schedule | 20 |
| day-parting-controller | 17 |
| report-export-controller | 16 |
| Sov Share Link | 10 |
| user-location-controller | 3 |
| 0-1CurrencyInfoController | 2 |
| health-controller | 1 |
| manual-edit-data-base-controller | 1 |
| profile-currency-controller | 1 |
| sync-task-controller | 1 |

## 二、部分无流量模块

| 模块(Tag) | 无流量/总数 |
|---|---|
| report-controller | 37/38 |
| category-controller | 16/17 |
| rule-controller | 14/15 |
| dashboard-controller | 8/9 |
| tag-report-controller | 9/11 |
| rule-apply-v-2-controller | 6/8 |
| bid-multiplier-controller | 3/5 |
| line-items-controller | 34/62 |
| NegativeKeyword相关接口 | 7/13 |
| 1-sharelink | 5/10 |
| event-controller | 2/4 |
| tag-rule-controller | 5/10 |
| user-controller | 21/50 |
| Keyword相关接口 | 7/18 |
| operation-log-controller | 4/11 |
| campaigns-controller | 8/25 |
| budget-line-item-controller | 4/15 |
| sov-controller | 1/4 |
| notification-controller | 1/7 |
| default-report-controller | 8/58 |
| Default Report异步下载接口 | 1/11 |
| rule-apply-controller | 2/24 |
| advertising-controller | 4/51 |
| 提供给下载中心的查询接口 | 2/26 |
| advertising模块异步下载接口 | 1/14 |

## 三、无流量接口明细（按模块）

### 0-1CurrencyInfoController　(2/2)
- `GET    /currency/exchange/rate`
- `GET    /currency/exists/list`

### 1-Schedule　(20/20)
- `DELETE /schedule/apply/batchDelete`
- `DELETE /schedule/apply/delete/{applyId}`
- `DELETE /schedule/template/batchDelete`
- `DELETE /schedule/template/delete/{tempId}`
- `GET    /schedule/get/lineItem/{lineItemId}`
- `GET    /schedule/getOwners`
- `GET    /schedule/run/autoRefill/{tempId}`
- `GET    /schedule/run/setting/{tempId}`
- `GET    /schedule/template/{tempId}`
- `POST   /schedule/apply/download`
- `POST   /schedule/apply/item/tag/tree`
- `POST   /schedule/apply/item/tree`
- `POST   /schedule/apply/page`
- `POST   /schedule/check/lineItems`
- `POST   /schedule/template/download`
- `POST   /schedule/template/page`
- `PUT    /schedule/apply/edit`
- `PUT    /schedule/edit/lineItems`
- `PUT    /schedule/template/batchEdit/state`
- `PUT    /schedule/template/edit`

### 1-sharelink　(5/10)
- `POST   /sharelink/delete`
- `POST   /sharelink/editDateRange`
- `POST   /sharelink/editDescription`
- `POST   /sharelink/editExpiredDate`
- `POST   /sharelink/export`

### Default Report异步下载接口　(1/11)
- `POST   /api/default/campaignTag/export/async`

### Keyword相关接口　(7/18)
- `PATCH  /keyword/bid`
- `PATCH  /keyword/bid/v2`
- `PATCH  /stemmedKeyword/bidAll/v2`
- `POST   /Keyword`
- `POST   /KeywordAll/v2`
- `POST   /checkKeywordAll`
- `POST   /keyword/status`

### NegativeKeyword相关接口　(7/13)
- `POST   /keyword/campaigns`
- `POST   /keyword/lineItems`
- `POST   /keyword/profiles`
- `POST   /negativeKeyword`
- `POST   /negativeKeyword/export`
- `POST   /negativeKeyword/status`
- `POST   /negativeKeywordAll/v2`

### Sov Share Link　(10/10)
- `GET    /sov/sharelink/get`
- `GET    /sov/sharelink/get/{id}`
- `GET    /sov/sharelink/getToken`
- `POST   /sov/sharelink/delete`
- `POST   /sov/sharelink/editDateRange`
- `POST   /sov/sharelink/editDescription`
- `POST   /sov/sharelink/editExpiredDate`
- `POST   /sov/sharelink/export`
- `POST   /sov/sharelink/modify`
- `POST   /sov/sharelink/search`

### advertising-controller　(4/51)
- `POST   /api/Report/HeatMap`
- `POST   /api/Report/getKeywordNames`
- `POST   /api/Report/getKeywordTableProductEnvData`
- `POST   /api/Report/lineItemHourly`

### advertising模块异步下载接口　(1/14)
- `POST   /api/report/keywordExplorer/export/async`

### bid-multiplier-controller　(3/5)
- `GET    /lineItem/bid-multiplier/{lineItemId}`
- `POST   /lineItems/bidMultiplier`
- `POST   /lineItems/bidMultiplierAll/v2`

### budget-line-item-controller　(4/15)
- `GET    /budget/user/default/currency`
- `POST   /budget/getLineItems`
- `POST   /budget/lineItem/list`
- `POST   /budget/report/lineItem`

### campaigns-controller　(8/25)
- `PATCH  /campaigns/attributionWindow`
- `PATCH  /campaigns/budget`
- `PATCH  /campaigns/dailyBudget`
- `PATCH  /campaigns/endDate`
- `PATCH  /campaigns/monthlyBudget`
- `POST   /campaigns/addToBalance`
- `POST   /campaigns/removeFromBalance`
- `POST   /campaigns/setBulkTarget`

### category-controller　(16/17)
- `DELETE /category/keyword/{id}`
- `DELETE /category/{categoryId}/retailer/{id}`
- `DELETE /category/{id}`
- `GET    /category/keyword/{keywordId}/status`
- `GET    /category/tree`
- `GET    /category/{categoryId}/retailer/list`
- `GET    /category/{categoryId}/retailer/{retailerId}/status`
- `GET    /category/{categoryId}/status`
- `POST   /category`
- `POST   /category/byItem`
- `POST   /category/keyword`
- `POST   /category/keyword/list`
- `POST   /category/list`
- `POST   /category/retailer`
- `POST   /multi/category/keyword/list`
- `PUT    /category/{id}`

### dashboard-controller　(8/9)
- `POST   /report/dashboard`
- `POST   /report/dashboard/byWeekDay`
- `POST   /report/dashboard/chart`
- `POST   /report/dashboard/keyword`
- `POST   /report/dashboard/monthOverMonth`
- `POST   /report/dashboard/pageType`
- `POST   /report/dashboard/productCategory`
- `POST   /report/dashboard/weekOverWeek`

### day-parting-controller　(17/17)
- `GET    /dayparting/getOwners`
- `GET    /dayparting/getTemplates`
- `GET    /dayparting/{templateId}`
- `POST   /dayparting/apply`
- `POST   /dayparting/applyTemplate`
- `POST   /dayparting/changeStatus`
- `POST   /dayparting/checkLineItemAvailableByApplyIds`
- `POST   /dayparting/checkLineItemAvailableByTempIds`
- `POST   /dayparting/deleteApply`
- `POST   /dayparting/deleteTemplate`
- `POST   /dayparting/downloadApply`
- `POST   /dayparting/downloadTemplate`
- `POST   /dayparting/lineItem/tree`
- `POST   /dayparting/lineItemTag/tree`
- `POST   /dayparting/setTemplateAndApply`
- `POST   /dayparting/templates`
- `POST   /dayparting/updateTemplate`

### default-report-controller　(8/58)
- `POST   /api/report/default/assistedSales/getDistributionByCampaignChartPerformance`
- `POST   /api/report/default/assistedSales/getDistributionByCampaignPerformance`
- `POST   /api/report/default/assistedSales/getDistributionByKeywordChartPerformance`
- `POST   /api/report/default/assistedSales/getDistributionByKeywordPerformance`
- `POST   /api/report/default/assistedSales/getDistributionByKeywordPerformanceDownload`
- `POST   /api/report/default/assistedSales/getDistributionByLineItemChartPerformance`
- `POST   /api/report/default/assistedSales/getDistributionByLineItemPerformance`
- `POST   /api/report/default/keyword/getKeywordDailyPerformanceTrend`

### event-controller　(2/4)
- `POST   /event/eventLog`
- `POST   /event/eventLog/detail`

### health-controller　(1/1)
- `GET    /health`

### line-items-controller　(34/62)
- `DELETE /lineItems/remove/products`
- `DELETE /lineItems/{lineItemId}/products`
- `GET    /lineItems/dayparting`
- `GET    /lineItems/dayparting/run/test/{lineItemId}`
- `GET    /lineItems/dayparting/timezone`
- `GET    /lineItems/states`
- `GET    /lineItems/{level}/getMinBidChangeSetting`
- `GET    /lineItems/{lineItemId}`
- `GET    /lineItems/{lineItemId}/products/max/minBid`
- `PATCH  /lineItems/budget`
- `PATCH  /lineItems/budgetAll/v2`
- `PATCH  /lineItems/dailyBudgetAll`
- `PATCH  /lineItems/maxBid`
- `PATCH  /lineItems/maxBidAll/v2`
- `PATCH  /lineItems/monthlyBudgetAll`
- `PATCH  /lineItems/status`
- `PATCH  /lineItems/targetBid`
- `PATCH  /lineItems/targetBidAll/v2`
- `POST   /lineItemTag/dayparting`
- `POST   /lineItemTag/getBulkTagDayparting`
- `POST   /lineItems/checkLineItemAvailableByLineItemIds`
- `POST   /lineItems/checkNames/{profileId}`
- `POST   /lineItems/createHistory`
- `POST   /lineItems/dayparting`
- `POST   /lineItems/getBulkDayparting`
- `POST   /lineItems/getConflictTagInfo`
- `POST   /lineItems/setMinBidChangeNotification`
- `POST   /lineItems/tagdayparting`
- `PUT    /lineItems/bulk/products`
- `PUT    /lineItems/bulk/productsAll/v2`
- `PUT    /lineItems/products/bulk/bid`
- `PUT    /lineItems/products/status`
- `PUT    /lineItems/{lineItemId}/products`
- `PUT    /lineItems/{lineItemId}/productsAll/v2`

### manual-edit-data-base-controller　(1/1)
- `PATCH  /manual/edit/lineItems/status`

### my-report-controller　(25/25)
- `DELETE /my-report/{reportId}`
- `GET    /my-report/fix-column/{type}`
- `GET    /my-report/getCategorys`
- `GET    /my-report/getOwners`
- `GET    /my-report/getProfileIdsByUserId/{userId}`
- `GET    /my-report/getRetailerContainsTargetByUserId/{userId}`
- `GET    /my-report/getUsersByClientId/{clientId}`
- `GET    /my-report/history/download/{historyId}`
- `GET    /my-report/history/email/{historyId}`
- `GET    /my-report/history/preview/{historyId}`
- `GET    /my-report/{reportId}`
- `GET    /my-report/{reportId}/preview`
- `GET    /my-report/{reportId}/runNow`
- `GET    /my-report/{reportId}/status`
- `POST   /my-report`
- `POST   /my-report/ftp/check`
- `POST   /my-report/ftp/private-key/upload`
- `POST   /my-report/getData`
- `POST   /my-report/getProfileByProfileIds`
- `POST   /my-report/history/list`
- `POST   /my-report/list`
- `POST   /my-report/preview/before`
- `POST   /my-report/s3/check`
- `POST   /my-report/transferMyReport`
- `PUT    /my-report/{reportId}`

### notification-controller　(1/7)
- `GET    /notification/productStockNotify/custom`

### operation-log-controller　(4/11)
- `GET    /bulk/import/error/{fileId}`
- `GET    /operationLog/{logId}`
- `POST   /bulk/download/failureResult/bulkUpdateCampaign`
- `POST   /createSuperWizardItems/{logId}`

### profile-currency-controller　(1/1)
- `POST   /profile/currency`

### report-controller　(37/38)
- `DELETE /report/filters/{id}`
- `GET    /report/customTablePlan`
- `GET    /report/filters`
- `GET    /report/taskChain`
- `GET    /report/taskChain/close`
- `GET    /report/taskChain/terminal`
- `GET    /report/taskChain/{taskChainId}`
- `POST   /report/campaign`
- `POST   /report/campaign/campaignByPageType`
- `POST   /report/campaign/export`
- `POST   /report/campaignChart`
- `POST   /report/customTablePlan`
- `POST   /report/default/VaynerMediaCampaignTag`
- `POST   /report/default/campaign`
- `POST   /report/default/getVMCampaignTag`
- `POST   /report/default/keyword`
- `POST   /report/default/lineItem`
- `POST   /report/default/product`
- `POST   /report/default/profile/brief`
- `POST   /report/default/profile/trend`
- `POST   /report/filters`
- `POST   /report/keyword`
- `POST   /report/keyword/export`
- `POST   /report/keywordChart`
- `POST   /report/lineItem/export`
- `POST   /report/lineItemChart`
- `POST   /report/pageType`
- `POST   /report/pageType/export`
- `POST   /report/product`
- `POST   /report/product/export`
- `POST   /report/productChart`
- `POST   /report/productLandscape`
- `POST   /report/productLandscape/export`
- `POST   /report/productLandscape/lineItemChart`
- `POST   /report/profile`
- `POST   /report/profile/export`
- `PUT    /report/filters/{id}`

### report-export-controller　(16/16)
- `POST   /dashboard/export/all`
- `POST   /dashboard/export/budgetHit`
- `POST   /dashboard/export/category-performance`
- `POST   /dashboard/export/keyword`
- `POST   /dashboard/export/page-type-performance`
- `POST   /dashboard/export/product`
- `POST   /report/default/VaynerMediaCampaignTag/export`
- `POST   /report/default/campaign/export`
- `POST   /report/default/keyword/export`
- `POST   /report/default/lineItem/export`
- `POST   /report/default/product/export`
- `POST   /report/default/profile/export`
- `POST   /sov/brand/export`
- `POST   /sov/keyword/export`
- `POST   /sov/product/analysis/export`
- `POST   /sov/product/export`

### rule-apply-controller　(2/24)
- `POST   /apply/changeLeader`
- `POST   /apply/pageTypes`

### rule-apply-v-2-controller　(6/8)
- `POST   /apply/v2/bulk/confirmProfiles`
- `POST   /apply/v2/bulkSaveUserProfiles`
- `POST   /apply/v2/changeLeader`
- `POST   /apply/v2/saveAdminProfiles`
- `POST   /apply/v2/saveUserProfiles`
- `POST   /apply/v2/updateSuperior`

### rule-controller　(14/15)
- `GET    /rule/getProductTag`
- `POST   /rule/add`
- `POST   /rule/changeStatus`
- `POST   /rule/edit`
- `POST   /rule/getCampaigns`
- `POST   /rule/getLineItems`
- `POST   /rule/getOwners`
- `POST   /rule/getPreview`
- `POST   /rule/logs`
- `POST   /rule/logs/getDetails`
- `POST   /rule/run`
- `POST   /rule/runNow/{ruleId}`
- `POST   /rule/search`
- `POST   /rule/{ruleId}`

### sov-controller　(1/4)
- `GET    /sov/product/list`

### sync-task-controller　(1/1)
- `GET    /task/query`

### tag-report-controller　(9/11)
- `POST   /report/tag/campaign/chart`
- `POST   /report/tag/campaign/export`
- `POST   /report/tag/campaign/list`
- `POST   /report/tag/lineItem/chart`
- `POST   /report/tag/lineItem/export`
- `POST   /report/tag/lineItem/list`
- `POST   /report/tag/product/chart`
- `POST   /report/tag/product/export`
- `POST   /report/tag/product/list`

### tag-rule-controller　(5/10)
- `GET    /tagRule/run/Campaign`
- `GET    /tagRule/run/LineItem`
- `GET    /tagRule/run/Product`
- `POST   /tagRule/changeStatus`
- `POST   /tagRule/run/{type}`

### user-controller　(21/50)
- `DELETE /user/deleteUserProfiles/{userId}`
- `GET    /user/consentUrl`
- `GET    /user/countries`
- `GET    /user/countriesSelectedNotice`
- `GET    /user/default/currency`
- `GET    /user/getBalances/export`
- `GET    /user/getEditableUserList`
- `GET    /user/getUserInfo`
- `GET    /user/getUserList`
- `GET    /user/menus`
- `GET    /user/notReceiveMinBidNotice`
- `GET    /user/notReceiveNotice`
- `GET    /user/receiveMinBidNotice`
- `GET    /user/receiveNotice`
- `GET    /user/widgets`
- `POST   /user/currency/save`
- `POST   /user/getCampaigns/tag`
- `POST   /user/getProductTagOwners`
- `POST   /user/oauth/callback`
- `POST   /user/saveUserProfiles`
- `POST   /user/widgets`

### user-location-controller　(3/3)
- `DELETE /user-location`
- `GET    /user-location`
- `POST   /user-location`

### 提供给下载中心的查询接口　(2/26)
- `POST   /async/download/default/campaignTag/report`
- `POST   /async/download/keywordExplorer/report`
