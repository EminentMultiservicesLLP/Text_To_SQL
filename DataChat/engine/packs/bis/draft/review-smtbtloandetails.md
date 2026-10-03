# Review: add `public.smtbtloandetails` to bis as area `loan`

## What will be added

```yaml
areas:
  loan:
    label: TODO Smtbtloandetails
    fact: loan
    synonyms:
    - TODO
    default_metric: loan_count
    metrics:
      loan_count:
        expr: COUNT(*)
        label: Number of smtbtloandetails rows
        format: integer
        synonyms:
        - TODO
      loan_interestrate:
        expr: SUM({loan.interestrate})
        label: Interestrate
        format: number
        synonyms:
        - TODO
      loan_loanamount:
        expr: SUM({loan.loanamount})
        label: Loanamount
        format: number
        synonyms:
        - TODO
      loan_alreadydedprincipal:
        expr: SUM({loan.alreadydedprincipal})
        label: Alreadydedprincipal
        format: number
        synonyms:
        - TODO
      loan_alreadydedinterest:
        expr: SUM({loan.alreadydedinterest})
        label: Alreadydedinterest
        format: number
        synonyms:
        - TODO
      loan_balanceprincipal:
        expr: SUM({loan.balanceprincipal})
        label: Balanceprincipal
        format: number
        synonyms:
        - TODO
      loan_permonthamt:
        expr: SUM({loan.permonthamt})
        label: Permonthamt
        format: number
        synonyms:
        - TODO
      loan_recoveredamt:
        expr: SUM({loan.recoveredamt})
        label: Recoveredamt
        format: number
        synonyms:
        - TODO
      loan_formfeeamt:
        expr: SUM({loan.formfeeamt})
        label: Formfeeamt
        format: number
        synonyms:
        - TODO
      loan_buildingfundamt:
        expr: SUM({loan.buildingfundamt})
        label: Buildingfundamt
        format: number
        synonyms:
        - TODO
    examples:
    - TODO
    time_column: loan.startdate
```

Joins: empid → emp, brlocid → br

## Figures from the database

- Number of smtbtloandetails rows: 2,148,095
- Number of smtbtloandetails rows by branch: 1 (top row: AGRA BRANCH)
- Interestrate: 144,198
- Interestrate by branch: 12 (top row: AGRA BRANCH)
- Loanamount: 2,984,456,669.31
- Loanamount by branch: 60,000 (top row: AGRA BRANCH)
- Alreadydedprincipal: 9,549,217.25
- Alreadydedprincipal by branch: 0 (top row: AGRA BRANCH)
- Alreadydedinterest: 83,076
- Alreadydedinterest by branch: 0 (top row: AGRA BRANCH)
- Balanceprincipal: 1,860,964,725.61
- Balanceprincipal by branch: 60,000 (top row: AGRA BRANCH)
- Permonthamt: 2,522,325,721.36
- Permonthamt by branch: 2,500 (top row: AGRA BRANCH)
- Recoveredamt: 2,981,447.2
- Recoveredamt by branch: None (top row: AGRA BRANCH)
- Formfeeamt: 597,641
- Formfeeamt by branch: 0 (top row: AGRA BRANCH)
- Buildingfundamt: 558,156.12
- Buildingfundamt by branch: 50 (top row: AGRA BRANCH)

## Test questions (built-in rules; the model is tested on the server)

- none

## Please confirm

- The local model could not be used ([WinError 10061] No connection could be made because the target machine actively refused it); the draft has TODO wording to fill in by hand.
- What one row means (an event with a date, or a current state such as a membership). For a current state, mark its measures `snapshot: true`.
- Labels and synonyms in the business's own words.
- Rows that should never count (cancelled, deleted, test) as `default_filters`.
- Dates before 1990 or far in the future: exclude them, or tell users the figure includes them.
- Links below 95% match: rows without a match drop out of any grouping on that link.
- Whether any column is sensitive (salary, personal data) and must stay out.

## Data profile

Rows: 2,148,095. Alias: `loan`.

### Links to tables already in the pack

| Column | Points at | Filled | Found | Match | Used |
|---|---|---:|---:|---:|---|
| `empid` | `emp.empid` | 2,148,095 | 2,134,312 | 99.4% | yes |
| `brlocid` | `br.brlocid` | 2,148,095 | 2,146,653 | 99.9% | yes |

Groupings reachable: branch, designation, department.

### Keys

| Column | Distinct values | Rows per value |
|---|---:|---:|
| `empid` | 278,084 | 7.72 |
| `brlocid` | 822 | 2613.25 |
| `loanid` | 2,148,095 | 1.00 |

### Date columns

| Column | Earliest | Latest | Empty | Before 1990 | Over 1 year ahead |
|---|---|---|---:|---:|---:|
| `loandate` | 1900-01-01 00:00:00 | 5201-02-26 00:00:00 | 286 | 12 | 12 |
| `startdate` | 1900-03-01 00:00:00 | 5201-02-01 00:00:00 | 0 | 8 | 9 |
| `enddate` | 1900-03-01 00:00:00 | 5201-02-28 00:00:00 | 6,776 | 11 | 137 |
| `datecreated` | 2009-12-23 16:23:37.233000 | 2027-06-10 00:00:00 | 286 | 0 | 0 |
| `datelastmod` | 2009-12-23 16:33:54.877000 | 2026-08-31 02:02:18.165939 | 1,764,253 | 0 | 0 |
| `feesfunddate` | 1900-01-01 00:00:00 | 2202-02-22 00:00:00 | 1,833,655 | 308,656 | 2 |

### Number columns

| Column | Min | Max | Total | Zero | Empty |
|---|---:|---:|---:|---:|---:|
| `interestrate` | 0.00 | 12.00 | 144198.00 | 2,136,078 | 0 |
| `loanamount` | 0.00 | 1826000.00 | 2984456669.31 | 7,017 | 0 |
| `alreadydedprincipal` | 0.00 | 135000.00 | 9549217.25 | 2,145,989 | 0 |
| `alreadydedinterest` | 0.00 | 20000.00 | 83076.00 | 2,148,048 | 0 |
| `balanceprincipal` | -13749.00 | 1250000.00 | 1860964725.61 | 350,122 | 0 |
| `permonthamt` | -3690.00 | 1057194.38 | 2522325721.36 | 3,817 | 0 |
| `recoveredamt` | 0.00 | 82000.00 | 2981447.20 | 2,102,433 | 44,132 |
| `formfeeamt` | 0.00 | 10940.00 | 597641.00 | 2,145,530 | 0 |
| `buildingfundamt` | -1440.00 | 11040.00 | 558156.12 | 2,144,548 | 0 |

### Flag-like columns (value: rows)

- `loan.interestcalc`: '3': 2,136,010, '1': 12,085
- `loan.deductiontype`: '1': 2,103,253, '2': 44,842
- `loan.loanacctno`: None: 1,828,395, '0': 319,695, '': 5
- `loan.loanpayby`: '0': 2,147,750, '1': 345
- `loan.loantype`: None: 1,838,751, '1': 309,340, '0': 4
- `loan.postedstatus`: None: 1,838,751, '1': 168,524, '0': 140,820
- `loan.iscarryforward`: 'False': 2,148,059, 'True': 36
- `emp.isofficestaff`: '0': 2,095,841, '1': 38,471
- `emp.active`: '0': 1,570,056, '1': 564,256
- `emp.issalaryfromhr`: '0': 2,134,191, '1': 121
- `emp.ubs`: 'N': 2,102,401, ' ': 31,623, 'Y': 288
- `emp.sdremark`: None: 2,082,290, '': 52,021, 'ONLY PAY FOR DEPOSIT': 1
- `br.zoneid`: '2': 1,459,642, '3': 398,857, '4': 174,759, '1': 113,393, '0': 2
- `br.ishoro`: '0': 1,767,306, '1': 379,347
- `br.attstafftimelock`: None: 1,968,544, '10 AM': 166,919, '11 AM': 11,150, '12 AM': 40
