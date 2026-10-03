# Scenario results: bis (llm-primary)

6/17 passed. Date used as today: 2026-10-01.

| Id | Group | Question | Result | Seconds | Reading / problem |
|---|---|---|---|---|---|
| B09 | Filters | active security guards in Lucknow branch | PASS | 114.3 | Understood as: Active employees, only Branch LUCKNOW BRANCH, only Designation SECURITY GUARD. |
| F06 | Dates | billing today | **FAIL** | 24.0 | type is unsupported, expected answer |
| G02 | Threshold | customers whose collection is less than 1 lakh this financial year | PASS | 18.5 | Understood as: Collection % and Amount received and Billing amount by Customer, FY 2026-27, where collection % is less than 100000.0%. |
| G03 | Threshold | states with billing between 10 and 50 crore last financial year | **FAIL** | 28.2 | type is unsupported, expected answer |
| H03 | Compare periods | billing growth in june 2026 compared to june 2025 | PASS | 18.8 | Understood as: Collection % and Amount received and Billing amount, June 2026 compared with June 2025. |
| I01 | Compare names | compare billing of lucknow branch and bhopal branch in june 2026 | PASS | 21.4 | Understood as: Billing amount by Branch, June 2026, only Branch LUCKNOW BRANCH, BHOPAL BRANCH. |
| I02 | Compare names | maharashtra vs gujarat billing this financial year | **FAIL** | 22.4 | type is unsupported, expected answer |
| J01 | Cross data | billing vs collection by branch for june 2026 | **FAIL** | 14.8 | metrics ['receipt_amount'] lacks ['billing_amount']; more ['billing.billing_amount'] lacks ['receipts.receipt_amount'] |
| J03 | Cross data | outstanding of blink commerce this financial year | **FAIL** | 11.9 | derived ['collection_efficiency'] lacks ['billing_minus_receipts']; notes lack 'not the ledger outstanding' |
| J05 | Cross data | billing and invoice value for june 2026 | **FAIL** | 14.9 | metrics ['invoice_value'] lacks ['billing_amount']; more ['billing.billing_amount'] lacks ['invoices.invoice_value'] |
| K01 | Counts | how many customers were billed in june 2026 | **FAIL** | 11.6 | metrics ['invoice_count'] lacks ['count:customer'] |
| K02 | Counts | number of branches with receipts this financial year | **FAIL** | 11.2 | metrics ['receipt_count'] lacks ['count:branch'] |
| L01 | Share | share of each state in billing this financial year | PASS | 11.6 | Understood as: Billing amount by State, FY 2026-27, with each one's share of the total. |
| P02 | Hinglish/Marathi | is saal ki billing har state | **FAIL** | 21.5 | type is unsupported, expected answer |
| P04 | Hinglish/Marathi | july 2026 madhe 50 lakh peksha jast collection asnare customers | **FAIL** | 19.6 | type is clarify, expected answer |
| P06 | Hinglish/Marathi | is saal top 5 customer billing | **FAIL** | 28.7 | type is unsupported, expected answer |
| U01 | Freshness | billing last month | PASS | 24.1 | Understood as: Billing amount, September 2026. |
