## ACC-022 Verification: Multi-Currency

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps MultiCurrencyTab in DashboardLayout | Structure | VERIFIED | MultiCurrencyPage.tsx:6-25 |
| 2 | Fetches currencies filtered by business_id, ordered by is_base_currency | Data | VERIFIED | useMultiCurrency.tsx:27-31 |
| 3 | Identifies base currency | Logic | VERIFIED | useMultiCurrency.tsx:36-37 |
| 4 | Add Currency dialog with 4 fields | UI | VERIFIED | MultiCurrencyTab.tsx:66-119 |
| 5 | Currency code uppercased on input | Logic | VERIFIED | MultiCurrencyTab.tsx:78 - `e.target.value.toUpperCase()` |
| 6 | Currency table with 7 columns | UI | VERIFIED | MultiCurrencyTab.tsx:126-195 |
| 7 | Inline exchange rate edit via onBlur | Feature | VERIFIED | MultiCurrencyTab.tsx:159-164 |
| 8 | updateExchangeRate updates rate and last_updated | Logic | VERIFIED | useMultiCurrency.tsx:82-107 |
| 9 | Refresh button re-saves same rate instead of fetching live rates | Bug | VERIFIED | MultiCurrencyTab.tsx:185 - `onClick={() => handleUpdateRate(currency.id, currency.exchange_rate)}` - passes current rate back |
| 10 | refreshRates function exists in hook but unused by component | Gap | VERIFIED | useMultiCurrency.tsx:115-141 provides `refreshRates`, component destructures only `{ currencies, baseCurrency, loading, addCurrency, updateExchangeRate }` at line 22 |
| 11 | convertAmount function exists in hook but unused | Gap | VERIFIED | useMultiCurrency.tsx:143-154 provides `convertAmount`, not used by component |
| 12 | Hardcoded neutral-300 borders | UI | VERIFIED | MultiCurrencyTab.tsx:125-134 - uses `border-neutral-300` instead of `border-border` |

### FALSIFIED Claims (Bugs)
1. **Refresh button is non-functional:** The RefreshCw button passes `currency.exchange_rate` (the current value) back to `handleUpdateRate`, which calls `updateExchangeRate(currencyId, newRate)`. Since newRate === current rate, this is a no-op that updates `last_updated` timestamp but doesn't change the rate. The hook's actual `refreshRates` function (which calls an external API) is never wired up.

### PARTIAL Claims
None.

### Summary
- Total claims: 12
- VERIFIED: 11
- PARTIAL: 0
- FALSIFIED: 1 (refresh button saves same rate)
- UNVERIFIABLE: 0
