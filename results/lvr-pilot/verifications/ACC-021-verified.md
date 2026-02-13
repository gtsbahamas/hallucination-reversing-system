## ACC-021 Verification: Fixed Assets

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps FixedAssetsTab in DashboardLayout | Structure | VERIFIED | FixedAssetsPage.tsx:6-25 |
| 2 | Fetches fixed_assets filtered by business_id | Data | VERIFIED | useFixedAssets.tsx:26-30 |
| 3 | Asset table with 8 columns | UI | VERIFIED | FixedAssetsTab.tsx:180-241 |
| 4 | Current value = max(price - depreciation, salvage) | Logic | VERIFIED | FixedAssetsTab.tsx:196 |
| 5 | Depreciation uses (price-salvage)/(life*12) per month | Logic | VERIFIED | useFixedAssets.tsx:149-157 |
| 6 | Months elapsed uses 30-day approximation | Logic | VERIFIED | useFixedAssets.tsx:152 - `(today.getTime() - purchaseDate.getTime()) / (1000 * 60 * 60 * 24 * 30)` |
| 7 | Add Asset dialog with form fields | UI | VERIFIED | FixedAssetsTab.tsx:75-176 |
| 8 | Insert sets current_value = purchase_price | Logic | VERIFIED | useFixedAssets.tsx:55 |
| 9 | Depreciation schedule generated as monthly rows | Logic | VERIFIED | useFixedAssets.tsx:82-118 |
| 10 | Only straight-line despite depreciation_method field | Gap | VERIFIED | useFixedAssets.tsx:86-88 - always uses straight-line formula, ignores depreciation_method |
| 11 | View button fetches schedule but no UI renders it | Scaffolding | VERIFIED | FixedAssetsTab.tsx:49-52 - calls `fetchDepreciationSchedule(asset.id)` which sets `depreciationSchedule` state in hook, but component never reads or renders this state |
| 12 | No edit/delete/dispose functionality | Gap | VERIFIED | No update or delete functions exist in hook or component |

### FALSIFIED Claims (Bugs)
1. **View depreciation button is non-functional:** The "View" button at line 229-234 calls `handleViewDepreciation` which fetches depreciation data and sets `selectedAsset` state. However, the component never renders the depreciation schedule data - there is no conditional UI that shows when `selectedAsset` is set. The data is fetched and discarded.

### PARTIAL Claims
None.

### Summary
- Total claims: 12
- VERIFIED: 11
- PARTIAL: 0
- FALSIFIED: 1 (View depreciation button fetches but never displays data)
- UNVERIFIABLE: 0
