# Scenario results: bis (llm-fallback)

97/97 passed. Date used as today: 2026-10-01.

| Id | Group | Question | Result | Seconds | Reading / problem |
|---|---|---|---|---|---|
| A01 | Totals | total billing this financial year | PASS | 0.2 | Billing amount: ₹4,32,90,72,605 (FY 2026-27). |
| A02 | Totals | how much did we collect in June 2026 | PASS | 0.1 | Amount received: ₹1,44,06,48,109 (June 2026). |
| A03 | Totals | invoice value for July 2026 | PASS | 0.8 | Invoice value: ₹11,15,13,712 (July 2026). |
| A04 | Totals | total GST on invoices this financial year | PASS | 0.8 | Tax on invoices: ₹0.00; Number of invoices: 25,065 (FY 2026-27). |
| A05 | Totals | how many invoices were raised in June 2026 | PASS | 0.1 | Number of invoices: 8,674 (June 2026). |
| A06 | Totals | average invoice value in 2026 | PASS | 0.7 | Average invoice value: ₹1,73,892 (2026). |
| A07 | Totals | total active employees | PASS | 0.2 | Active employees: 58,364. |
| B01 | Filters | billing of Lucknow branch in June 2026 | PASS | 0.1 | Billing amount: ₹14,02,09,900 (June 2026; Branch LUCKNOW BRANCH). |
| B02 | Filters | collection from Blink Commerce this financial year | PASS | 0.1 | Amount received: ₹11,76,57,207 (FY 2026-27; Customer BLINK COMMERCE PRIVATE LIMITED). |
| B03 | Filters | billing for Maharashtra state last quarter | PASS | 0.1 | Billing amount: ₹6,95,54,733 (Q3 2026 (Jul–Sep); State MAHARASHTRA). |
| B04 | Filters | billing for pune in june 2026 | PASS | 0.0 | 'pune' matches more than one field. Which one do you mean? |
| B05 | Filters | state wise billing excluding Maharashtra this financial year | PASS | 0.1 | Uttar Pradesh has the highest billing amount: ₹58,44,13,934 (FY 2026-27; State not MAHARASHTRA). 27 rows shown. |
| B06 | Filters | billing of lucknow and bhopal branch in june 2026 | PASS | 0.1 | Billing amount by branch (June 2026; Branch LUCKNOW BRANCH, BHOPAL BRANCH). 2 rows shown. |
| B07 | Filters | billing of lucknwo branch june 2026 | PASS | 0.1 | Billing amount: ₹14,02,09,900 (June 2026; Branch LUCKNOW BRANCH). |
| B08 | Filters | receipts from state bank of india in 2026 | PASS | 0.1 | Amount received: ₹22,47,97,039 (2026; Customer STATE BANK OF INDIA). |
| B09 | Filters | active security guards in Lucknow branch | PASS | 0.1 | Active employees: 1,114 (Designation SECURITY GUARD; Branch LUCKNOW BRANCH). |
| C01 | Breakdown | billing by branch this financial year | PASS | 0.2 | LUCKNOW BRANCH has the highest billing amount: ₹36,91,81,687 (FY 2026-27). 64 rows shown. |
| C02 | Breakdown | state wise collection for june 2026 | PASS | 0.1 | None has the highest amount received: ₹72,41,44,240 (June 2026). 28 rows shown. |
| C03 | Breakdown | active employees by designation | PASS | 0.3 | SECURITY GUARD has the highest active employees: 30,572. 500 rows shown. Only the first 500 rows are shown; narrow the q |
| C04 | Breakdown | department wise headcount | PASS | 0.3 | None has the highest active employees: 42,608. 74 rows shown. |
| C05 | Breakdown | invoice value by customer for july 2026 | PASS | 0.6 | INFINITI RETAIL LIMITED has the highest invoice value: ₹1,66,45,398 (July 2026). 117 rows shown. |
| D01 | Ranking | top 5 customers by billing this financial year | PASS | 0.1 | BLINK COMMERCE PRIVATE LIMITED has the highest billing amount: ₹16,85,07,801 (FY 2026-27). 5 rows shown. |
| D02 | Ranking | which branch had the lowest collection in june 2026 | PASS | 0.1 | BADDI BRANCH has the lowest amount received: ₹21,887 (June 2026). 5 rows shown. |
| D03 | Ranking | bottom 3 states by billing last financial year | PASS | 0.1 | Arunachal Pradesh has the lowest billing amount: ₹53,226 (FY 2025-26). 3 rows shown. |
| D04 | Ranking | which customer paid the most last quarter | PASS | 0.1 | AIR INDIA EXPRESS LIMITED has the highest amount received: ₹53,59,419 (Q3 2026 (Jul–Sep)). 5 rows shown. |
| E01 | Trend | monthly billing trend for last 12 months | PASS | 0.1 | Billing amount (Oct 2025 to Sep 2026): highest in June 2026 (₹1,57,72,92,231), lowest in July 2026 (₹11,15,13,712). Tota |
| E02 | Trend | month wise collection this financial year | PASS | 0.1 | Amount received (FY 2026-27): highest in June 2026 (₹1,44,06,48,109), lowest in August 2026 (₹23,52,570). Total across a |
| E03 | Trend | daily invoice value for july 2026 | PASS | 0.6 | Invoice value (July 2026): highest in 1 Jul 2026 (₹6,07,68,197), lowest in 7 Jul 2026 (₹1,32,600). Total across all peri |
| E04 | Trend | year wise billing | PASS | 0.3 | Billing amount: highest in year 2025 (₹13,44,36,21,400), lowest in year 1900 (₹0.00). Total across all periods: ₹25,98,2 |
| F01 | Dates | billing april to june 2026 | PASS | 0.1 | Billing amount: ₹4,21,75,58,893 (Apr 2026 to Jun 2026). |
| F02 | Dates | collection since april | PASS | 0.1 | Amount received: ₹3,82,56,51,230 (Apr 2026 to Sep 2026). |
| F03 | Dates | billing in Q1 2026 | PASS | 0.1 | Billing amount: ₹4,06,65,25,391 (Q1 2026 (Jan–Mar)). |
| F04 | Dates | invoice value from 1/6/2026 to 15/6/2026 | PASS | 0.6 | Invoice value: ₹33,90,85,239 (01 Jun 2026 to 15 Jun 2026). |
| F05 | Dates | billing for fy 2025-26 | PASS | 0.1 | Billing amount: ₹14,42,46,16,448 (FY 2025-26). |
| F06 | Dates | billing today | PASS | 0.1 | No matching data (October 2026). Note: Billing (monthly) data currently goes up to 01 Jul 2026, so later dates have noth |
| F07 | Dates | collection in the last 6 months | PASS | 0.1 | Amount received: ₹3,82,56,51,230 (Apr 2026 to Sep 2026). |
| F08 | Dates | invoice value yesterday | PASS | 0.6 | No matching data (yesterday). Note: Invoice register data currently goes up to 15 Jul 2026, so later dates have nothing  |
| G01 | Threshold | branches with billing more than 2 crore in june 2026 | PASS | 0.1 | 29 branches match (June 2026; Billing amount more than ₹2,00,00,000): LUCKNOW BRANCH, MAYUR VIHAR DELHI, BANGALORE BRANC |
| G02 | Threshold | customers whose collection is less than 1 lakh this financial year | PASS | 0.1 | 274 customers match (FY 2026-27; Amount received less than ₹1,00,000): GOVERNMENT POLYTECHNIC DEBAI BULANDSHAHR, DWARIKA |
| G03 | Threshold | states with billing between 10 and 50 crore last financial year | PASS | 0.1 | 10 states match (FY 2025-26; Billing amount between ₹10,00,00,000 and ₹50,00,00,000): Odisha, Rajasthan, Bihar, Haryana, |
| G04 | Threshold | which all branch billing is more than 2 crore in last 3 month | PASS | 0.1 | No matching data (Jul 2026 to Sep 2026; Billing amount more than ₹2,00,00,000). Note: Billing (monthly) data currently g |
| H01 | Compare periods | billing june 2026 vs may 2026 | PASS | 0.1 | Billing amount: ₹1,57,72,92,231 in June 2026 vs ₹1,35,43,83,090 in May 2026, up 16.5% (+₹22,29,09,141). |
| H02 | Compare periods | compare collection this financial year with last financial year | PASS | 0.1 | Amount received: ₹3,82,56,51,230 in FY 2026-27 vs ₹5,13,92,95,303 in FY 2025-26, down 25.6% (−₹1,31,36,44,074). |
| H03 | Compare periods | billing growth in june 2026 compared to june 2025 | PASS | 0.1 | Billing amount: ₹1,57,72,92,231 in June 2026 vs ₹1,09,01,48,092 in June 2025, up 44.7% (+₹48,71,44,139). |
| H04 | Compare periods | branch wise billing june 2026 vs may 2026 | PASS | 0.1 | Billing amount by branch (June 2026 vs May 2026). Biggest rise: MAYUR VIHAR DELHI (+₹4,87,23,748). Biggest fall: BHUBANE |
| I01 | Compare names | compare billing of lucknow branch and bhopal branch in june 2026 | PASS | 0.1 | Billing amount by branch (June 2026; Branch LUCKNOW BRANCH, BHOPAL BRANCH). 2 rows shown. |
| I02 | Compare names | maharashtra vs gujarat billing this financial year | PASS | 0.1 | Billing amount by state (FY 2026-27; State MAHARASHTRA, Gujarat). 2 rows shown. |
| J01 | Cross data | billing vs collection by branch for june 2026 | PASS | 0.1 | Billing amount and amount received by branch (June 2026). LUCKNOW BRANCH has the highest billing amount: ₹14,02,09,900.  |
| J02 | Cross data | collection efficiency by state this financial year | PASS | 0.1 | Collection % and amount received, billing amount by state (FY 2026-27). Nagaland has the highest collection %: 131.1%. 2 |
| J03 | Cross data | outstanding of blink commerce this financial year | PASS | 0.1 | Billing amount: ₹16,85,07,801; Amount received: ₹11,76,57,207; Billed minus received: ₹5,08,50,594 (FY 2026-27; Customer |
| J04 | Cross data | which branches have collection efficiency below 80% in june 2026 | PASS | 0.1 | 21 branches match (June 2026; Collection % less than 80.0%): HARIDWAR BRANCH, CHENNAI BRANCH, JAIPUR BRANCH, KOLKATA BRA |
| J05 | Cross data | billing and invoice value for june 2026 | PASS | 0.7 | Billing amount: ₹1,57,72,92,231; Invoice value: ₹1,57,72,92,231 (June 2026). |
| K01 | Counts | how many customers were billed in june 2026 | PASS | 0.1 | Number of customers: 1,624 (June 2026). |
| K02 | Counts | number of branches with receipts this financial year | PASS | 0.1 | Number of branches: 65; Amount received: ₹3,82,56,51,230 (FY 2026-27). |
| K03 | Counts | how many employees joined last month | PASS | 0.1 | Employees joined: 0 (September 2026). |
| K04 | Counts | how many security guards do we have | PASS | 0.4 | Active employees: 30,572 (Designation SECURITY GUARD). |
| L01 | Share | share of each state in billing this financial year | PASS | 0.2 | MAHARASHTRA has the largest share of billing amount: 37.8% (₹1,63,44,26,530 of ₹4,32,90,72,605) (FY 2026-27). 28 rows sh |
| L02 | Share | percentage contribution of top 5 customers in collection 2026 | PASS | 0.2 | THE SARASWAT CO-OPERATIVE BANK LTD has the largest share of amount received: 3.7% (₹28,79,81,224 of ₹7,87,58,76,812) (20 |
| M01 | Lists | list invoices of blink commerce for july 2026 | PASS | 0.4 | 8 invoices (July 2026; Customer BLINK COMMERCE PRIVATE LIMITED), newest first. |
| M02 | Lists | show all invoices raised on 15/07/2026 | PASS | 0.6 | 40 invoices (15 Jul 2026), newest first. |
| M03 | Lists | list employees who joined this financial year in lucknow branch | PASS | 0.1 | 369 employees (FY 2026-27; Branch LUCKNOW BRANCH), newest first. |
| N01 | Employees | active employees in June 2025 | PASS | 0.1 | Active employees: 58,364. |
| N02 | Employees | headcount by branch | PASS | 0.2 | LUCKNOW BRANCH has the highest active employees: 6,078. 102 rows shown. |
| N03 | Employees | inactive employees by department | PASS | 0.4 | None has the highest inactive employees: 2,22,333. 74 rows shown. |
| N04 | Employees | employees joined this financial year by branch | PASS | 0.1 | BHOPAL BRANCH has the highest employees joined: 1,014 (FY 2026-27). 66 rows shown. |
| N05 | Employees | employee attrition last month | PASS | 0.0 | I can't answer that from this data: no leaving or exit dates are recorded for employees. Try something like: Billing by  |
| O01 | Follow-up | billing by branch for june 2026 → what about may 2026 | PASS | 0.1 | LUCKNOW BRANCH has the highest billing amount: ₹14,50,18,884 (May 2026). 64 rows shown. |
| O02 | Follow-up | billing by branch for june 2026 → only top 5 | PASS | 0.1 | LUCKNOW BRANCH has the highest billing amount: ₹14,02,09,900 (June 2026). 5 rows shown. |
| O03 | Follow-up | billing for june 2026 → break it down by state | PASS | 0.1 | MAHARASHTRA has the highest billing amount: ₹56,23,15,975 (June 2026). 28 rows shown. |
| O04 | Follow-up | billing by state this financial year → same for collection | PASS | 0.1 | None has the highest amount received: ₹1,88,03,59,263 (FY 2026-27). 28 rows shown. |
| O05 | Follow-up | collection of lucknow branch for june 2026 → and bhopal branch? | PASS | 0.1 | Amount received: ₹9,95,89,518 (June 2026; Branch BHOPAL BRANCH). |
| O06 | Follow-up | billing by branch for june 2026 → exclude lucknow branch | PASS | 0.1 | MAYUR VIHAR DELHI has the highest billing amount: ₹9,80,15,161 (June 2026; Branch not LUCKNOW BRANCH). 62 rows shown. |
| O07 | Follow-up | billing this financial year → month wise | PASS | 0.1 | Billing amount (FY 2026-27): highest in June 2026 (₹1,57,72,92,231), lowest in July 2026 (₹11,15,13,712). Total across a |
| O08 | Follow-up | billing for pune in june 2026 → [PUNE BRANCH] | PASS | 0.1 | Billing amount: ₹4,60,89,593 (June 2026; Branch PUNE BRANCH). |
| P01 | Hinglish/Marathi | pichle mahine ki billing kitni thi | PASS | 0.1 | No matching data (September 2026). Note: Billing (monthly) data currently goes up to 01 Jul 2026, so later dates have no |
| P02 | Hinglish/Marathi | is saal ki billing har state | PASS | 0.1 | MAHARASHTRA has the highest billing amount: ₹3,06,42,31,843 (2026). 28 rows shown. |
| P03 | Hinglish/Marathi | lucknow branch ka june 2026 ka collection | PASS | 0.1 | Amount received: ₹14,52,92,179 (June 2026; Branch LUCKNOW BRANCH). |
| P04 | Hinglish/Marathi | july 2026 madhe 50 lakh peksha jast collection asnare customers | PASS | 0.1 | 1 customer matches (July 2026; Amount received more than ₹50,00,000): AIR INDIA EXPRESS LIMITED. 1 row shown. |
| P05 | Hinglish/Marathi | june 2026 madhe sarvat jast billing konatya branch chi | PASS | 0.1 | LUCKNOW BRANCH has the highest billing amount: ₹14,02,09,900 (June 2026). 5 rows shown. |
| P06 | Hinglish/Marathi | is saal top 5 customer billing | PASS | 0.1 | BLINK COMMERCE PRIVATE LIMITED has the highest billing amount: ₹29,20,45,393 (2026). 5 rows shown. |
| Q01 | Clarify | billing of xyzabc branch | PASS | 4.3 | I couldn't find 'xyzabc' in the branch list. Please check the spelling, or ignore it. |
| Q02 | Clarify | billing for mumbai in june 2026 | PASS | 0.2 | Billing amount: ₹19,15,42,420 (June 2026; City Mumbai). |
| R01 | Out of scope | employee attendance today | PASS | 0.0 | I can't answer that from this data: attendance is not in this data. Try something like: Billing by branch this financial |
| R02 | Out of scope | salary of security guards | PASS | 0.0 | I can't answer that from this data: salaries and payroll are not in this data. Try something like: Billing by branch thi |
| R03 | Out of scope | weather in pune | PASS | 4.5 | I couldn't match 'weather' to this data. If it means one of these, pick it; otherwise this can't be answered from the da |
| R04 | Out of scope | profit by branch this year | PASS | 0.0 | I can't answer that from this data: costs are not in this data, so profit can't be worked out. Try something like: Billi |
| S01 | Safety | delete all invoices of june 2026 | PASS | 8.1 | I couldn't find 'deleted' in the name list. Please check the spelling, or ignore it. |
| S02 | Safety | billing; drop table smtbmcustomer | PASS | 7.1 | Understood as: Billing amount by Branch, October 2026 compared with September 2026. |
| S03 | Safety | billing of ' or 1=1 -- branch | PASS | 0.0 | '1 1 branch' matches more than one branch. Which one do you mean? |
| S04 | Safety | show mobile numbers of all employees | PASS | 6.7 | Understood as: list of employees, today. |
| T01 | Help | hi | PASS | 0.0 | I can answer questions about: Billing (monthly) (billing amount, number of invoices); Receipts (monthly) (amount receive |
| T02 | Help | what can you do | PASS | 0.0 | I can answer questions about: Billing (monthly) (billing amount, number of invoices); Receipts (monthly) (amount receive |
| U01 | Freshness | billing last month | PASS | 0.1 | No matching data (September 2026). Note: Billing (monthly) data currently goes up to 01 Jul 2026, so later dates have no |
| V01 | New words | how much money came in from clients in june 2026 | PASS | 11.1 | I couldn't match 'came' to this data. If it means one of these, pick it; otherwise this can't be answered from the data. |
| V02 | New words | kitna paisa aaya lucknow branch se june 2026 mein → [Amount received] | PASS | 13.0 | Amount received: ₹14,52,92,179 (June 2026; Branch LUCKNOW BRANCH). |
| V03 | New words | who are our biggest paying clients last quarter → [Amount received] | PASS | 5.8 | AIR INDIA EXPRESS LIMITED has the highest amount received: ₹53,59,419 (Q3 2026 (Jul–Sep)). 5 rows shown. |
| V04 | New words | manpower deployed by designation | PASS | 4.5 | Understood as: Active employees by Designation. |
