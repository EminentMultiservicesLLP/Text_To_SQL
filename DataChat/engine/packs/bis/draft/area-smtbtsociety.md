# Draft area: `public.smtbtsociety`

Rows: 344,898. Proposed alias: `soc`.

## Links to tables already in the pack

| Column | Points at | Filled | Found | Match | Proposed |
|---|---|---:|---:|---:|---|
| `brlocid` | `br.brlocid` | 344,898 | 344,898 | 100.0% | yes |
| `empid` | `emp.empid` | 344,898 | 337,765 | 97.9% | yes |

Groupings this area would reach: branch, designation, department.

## Keys

| Column | Distinct values | Rows per value |
|---|---:|---:|
| `brlocid` | 95 | 3630.51 |
| `empid` | 344,849 | 1.00 |
| `societyid` | 344,898 | 1.00 |

## Date columns

| Column | Earliest | Latest | Empty | Before 1990 | Over 1 year ahead |
|---|---|---|---:|---:|---:|
| `sctyjoindate` | 1900-01-01 00:00:00 | 5009-05-26 00:00:00 | 226 | 56 | 1 |
| `wefdate` | 1957-08-07 00:00:00 | 2026-08-31 00:00:00 | 8 | 31 | 0 |
| `datecreated` | 2009-11-24 16:10:29.483000 | 2026-08-31 22:07:27.962991 | 5,471 | 0 | 0 |
| `datelastmod` | 2009-12-11 17:30:16.770000 | 2026-08-31 22:10:31.314285 | 329,066 | 0 | 0 |

## Number columns (proposed as measures)

| Column | Min | Max | Total | Zero | Empty |
|---|---:|---:|---:|---:|---:|
| `entrancefee` | 0.00 | 31330.00 | 2691027.00 | 74,856 | 0 |
| `miscexpense` | 0.00 | 920.00 | 329383.00 | 75,834 | 0 |
| `sctycontribution` | 0.00 | 37000.00 | 42703642.00 | 715 | 0 |

## To decide before going live

- What one row means (an event with a date, or a current state such as a membership). For a current state, mark its measures `snapshot: true`.
- Labels and synonyms in the business's own words; replace every TODO.
- Rows that should never count (cancelled, deleted, test) as `default_filters`.
- Dates before 1990 or far in the future: exclude them, or tell users the figure includes them.
- Links below 95% match: rows without a match drop out of any grouping on that link.
- Whether any column is sensitive (salary, personal data) and must stay out.
- Grant read access: `GRANT SELECT ON public.smtbtsociety TO <read-only login>;`
- Add scenarios to scenarios/<client>.yaml and run tools/scenario_test.py.
