
# Test Compass
### From website performance signals to a practical A/B testing roadmap

Test Compass helps small and medium-sized e-commerce businesses use website performance data to prioritise investigations and develop structured website A/B test proposals.

It connects an interactive Tableau dashboard with a Streamlit workspace for managing a test backlog, planning experiments and recording learnings.

## Business problem

Small and medium-sized e-commerce businesses may have regular website traffic and someone managing their marketing, but no dedicated conversion rate optimisation (CRO) or analytics team.

Analytics show what happened. Turning those observations into an improvement programme requires further decisions:

- Which signals deserve investigation?
- What website change could address the problem?
- Is there enough eligible traffic to test that change?
- How will results inform future decisions?

Without a shared process, ideas can remain scattered, priorities unclear and learnings disconnected from subsequent work.

## Business question

**How can small and medium-sized e-commerce businesses use website performance data to prioritise investigations and manage a feasible roadmap of website A/B tests without dedicated analytics or CRO teams?**

The analysis addresses two supporting questions:

1. Where do sessions stop progressing through the recorded shopping journey?
2. Which visitor groups show the largest progression shortfalls when both session volume and comparison rates are considered?

## Proposed solution

Test Compass bridges performance analysis and the management of experimentation.

| Component | Purpose |
|---|---|
| **Tableau dashboard** | Explore performance, compare groups and identify ranked investigation signals. |
| **Test Backlog** | Review the evidence, document a proposed change and hypothesis, and assess priority. |
| **Test Planner** | Assess sample requirements, estimated duration and readiness. |
| **Test Learnings** | Organise experiment outcomes and conclusions for future decisions. |

A website A/B test proposal describes a specific change, its intended audience, a hypothesis and a measurable outcome. A future experiment would randomly assign eligible visitors to the original or changed experience.

The intended users are business owners and marketers, including freelancers, working without dedicated specialist teams. Test feasibility depends on eligible traffic, baseline performance and the effect the experiment is designed to detect.

## Data source

The project uses Google's public, obfuscated GA4 sample e-commerce dataset in BigQuery.

The dataset contains obfuscated event data from the Google Merchandise Store. It is public sample data, not data collected from a client or my own website.

The BigQuery source is:

`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

| Item | Scope |
|---|---|
| Period | 1 November 2020–31 January 2021 |
| Days covered | 92 |
| Dashboard population | 360,129 visitor–session pairs |
| Dashboard export | One row per visitor–session pair |
| Acquisition fields | First-user source and medium |

A **session** represents a recorded website visit. One person can have multiple sessions. The project identifies sessions using both `user_pseudo_id` and `session_id`.

Source and medium describe how users were first acquired. They do not necessarily identify how users arrived during the current session.

The sample demonstrates the workflow; it does not establish that the source business matches the intended customer profile.

[Google's dataset documentation](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset)

## Workflow and tools

```text
GA4 events in BigQuery
        ↓
SQL audit, session aggregation and funnel preparation
        ↓
Python validation and exploratory analysis
        ↓
Tableau performance dashboard and investigation signals
        ↓
Streamlit test backlog, planning and learnings prototype
```

- **SQL / BigQuery:** event audits, session preparation and analytical business logic.
- **Python / Jupyter:** export validation and exploratory analysis.
- **Tableau:** interactive performance analysis and opportunity presentation.
- **Streamlit:** demonstration of the testing-management workflow.
- **Git / GitHub:** version control and project documentation.

## Data preparation and analytical decisions

The preparation includes:

- Checking visitor, session and transaction identifiers.
- Excluding events without the identifiers required for session aggregation.
- Using the combined visitor–session key rather than counting session IDs alone.
- Preserving identifier columns as strings when loading exports into Python.
- Checking dataset dimensions, date coverage, missing values and duplicate session keys.
- Aggregating event records into session-level counts and flags.
- Constructing a strictly ordered, same-session funnel.
- Flagging timing and event-sequence anomalies rather than automatically deleting them.
- Retaining obscured acquisition labels without guessing their original values.
- Auditing purchase revenue and transaction identifiers before deciding which metrics to report.

Validation of the final dashboard export found 360,129 rows, 35 columns, 92 dates and no duplicate visitor–session keys.

### Ordered funnel definition

The funnel requires the following recorded sequence within the same session:

**Product view → Add to cart → Begin checkout → Purchase**

Each later event must have a strictly greater timestamp than the preceding qualifying event. Skipped or equal-timestamp stages do not satisfy the ordered sequence.

This is a session-level funnel, not an item-level funnel: the events do not necessarily concern the same product.

The overall purchasing-session metric counts sessions with at least one purchase event, regardless of whether they recorded the complete ordered funnel.

## Main findings

Across all dashboard sessions:

| Metric | Value |
|---|---:|
| Sessions | 360,129 |
| Purchasing sessions | 4,848 |
| Session purchase rate | 1.35% |
| Sessions reaching a product view | 77,020 |
| Sessions reaching cart after product view | 14,380 |
| Sessions reaching checkout after cart | 5,187 |
| Sessions reaching purchase after checkout | 2,778 |

Approximately 21.39% of all sessions recorded a product view.

Of the 4,848 purchasing sessions, 2,070 (42.7%) did not record the complete ordered funnel within one session. This describes recorded event coverage; it does not establish the route those customers actually followed.

## Opportunity ranking

The opportunity dataset compares each segment with the other named segments in the same dimension and funnel transition.

The comparison rate is calculated from the combined progressed and eligible session counts of those other segments. It is therefore weighted by session volume, rather than being a simple average of segment rates.

The ranking uses:

```text
Step rate = progressed sessions / eligible sessions

Comparison rate =
total progressed sessions in other named segments
/
total eligible sessions in those other named segments

Rate gap = comparison rate − step rate

Estimated progression gap =
eligible sessions × max(rate gap, 0)
```

Estimated progression gaps are ranked from largest to smallest using SQL `RANK()`. Equal values receive the same rank.

The gap in percentage points is `rate_gap × 100`.

“Sessions at step” means sessions eligible to enter that particular transition. For Product View → Add to Cart, it counts sessions that reached a product view, rather than all website sessions.

### Category selection

The preparation query classifies null or blank segment values as `Missing`.

The values `(data deleted)`, `<Other>`, `(none)` and `(not set)` are classified as `Unclear attribution`. The ranking query includes only categories classified as `Named value`.

This is an explicit selection rule for the ranking. In particular, `(none)` is not necessarily corrupted data; excluding it limits the medium comparison to the remaining named categories.

Excluded acquisition categories remain included in the overall dashboard session population.

### Highest-ranked signal

For First User Medium: organic, at Sessions → Product View:

- Eligible sessions: 122,841.
- Progressed sessions: 25,740.
- Segment progression rate: 20.95%.
- Comparison rate: 21.81%.
- Rate shortfall: 0.85 percentage points.
- Estimated progression gap: approximately 1,047 sessions.

The ranking combines session volume with underperformance against a benchmark. A smaller rate difference across a larger group can therefore rank above a larger difference across a smaller group.

The estimated gap is not predicted additional purchases, revenue or experiment uplift. Source and medium groups can overlap, so ranked rows do not automatically represent independent test ideas.

## Tableau dashboard

The dashboard includes:

- Session volume, purchasing sessions, purchase rate and date coverage.
- Performance trends.
- Device comparisons.
- A strictly ordered session funnel and transition drop-off rates.
- Three ranked investigation signals.
- Filters for exploring the session data.

The opportunity table uses a separate, pre-aggregated dataset with stored ranks. Dashboard filters should not be assumed to recalculate those ranks unless their behaviour has been verified.

## Streamlit prototype

Streamlit demonstrates how an analytics signal can become a structured website A/B test proposal.

The prototype contains:

- **Test Backlog:** signal evidence, diagnosis, proposed change, hypothesis and manual prioritisation.
- **Test Planner:** experiment-planning support.
- **Test Learnings:** a workflow for recording and reviewing experiment outcomes.

The app supports signal fields supplied through URL query parameters and provides a default example when those fields are absent.

For this single-user prototype, backlog records are saved to a local JSON file. Shared deployment would require an appropriate persistent storage solution.

No randomised experiment was conducted as part of this analysis. Planning functionality and example outcomes must not be interpreted as evidence that a proposed intervention works.

### Access

The Streamlit app currently runs locally. A `localhost` address is accessible only on the computer running the app.

To run it independently, follow the instructions below. A public application URL will be added if the prototype is deployed.

## Why verified revenue is not reported

The notebook audits 5,692 purchase-event rows. Although revenue values are present, transaction identifiers are not reliable for counting or deduplicating orders:

- `(not set)` appears on 883 purchase events.
- Some repeated transaction IDs have different revenue amounts.

An event-level revenue sum is therefore not presented as validated, transaction-deduplicated revenue.

The dashboard focuses on purchase activity, session purchase rate and funnel progression. It does not estimate financial returns from the ranked signals.

## Analysis scope and limitations

The current dashboard analysis is descriptive. It does not establish statistical significance or causation.

- The public dataset is obfuscated, and its internal consistency may be limited.
- Some acquisition values appear as `<Other>` or `(data deleted)`.
- Overall session metrics retain those sessions; the acquisition opportunity ranking uses the category-selection rules described above.
- First-user acquisition is different from current-session attribution.
- The store-domain source requires tracking validation before interpreting it as an actionable acquisition channel.
- Missing or out-of-order events can reflect customer behaviour, measurement limitations or sample obfuscation.
- The funnel does not capture every possible purchasing journey.
- Sessions from the same user may be related.
- No inferential significance test is claimed for the opportunity ranking.
- Estimated benchmark gaps are investigation aids, not forecasts.

## Earlier exploratory work

The notebook also contains an earlier analysis of 76,995 eligible product-view sessions, created while exploring a purchase-prediction direction.

That population and its purchase rate differ from the final all-session dashboard population. Its results should not be substituted for the dashboard's overall website metrics.

Query 02 supports this earlier exploration. It is not a required input to the final dashboard query.

The final project presented here follows the data-analytics and decision-support direction.

## Project structure

```text
testcompass/
├── README.md
├── sql/
│   ├── 01_ga4_audit_eda.sql
│   ├── 02_ga4_session_features.sql
│   ├── 03_ga4_dashboard_sessions_updated.sql
│   ├── 04_test_opportunity_candidates.sql
│   ├── 05_validate_test_opportunity_candidates.sql
│   └── 06_test_opportunity_signals_ranked.sql
├── notebooks/
│   └── 01_ga4_eda.ipynb
├── utilities/
│   └── export_ga4_dashboard_colab.ipynb
├── tableau/
│   └── TestCompass_Tableau_dashboard.twbx
├── streamlit_app/
│   └── app.py
├── presentation/
└── data/
    └── raw/ga4/
```

Raw data exports and local virtual environments are excluded from version control. Local export files are required to rerun the notebook sections that read them.

## Running the project

### SQL and data exports

Run the SQL in BigQuery against the public GA4 dataset. BigQuery access and a project for executing queries are required; query costs depend on the execution environment.

| Query | Purpose |
|---|---|
| `01_ga4_audit_eda.sql` | Audit raw events and identifiers. |
| `02_ga4_session_features.sql` | Prepare the earlier product-view exploration dataset. |
| `03_ga4_dashboard_sessions_updated.sql` | Produce the final session-level dashboard export and ordered-funnel fields. |
| `04_test_opportunity_candidates.sql` | Create the opportunity preparation table. |
| `05_validate_test_opportunity_candidates.sql` | Check eligible and progressed session counts. |
| `06_test_opportunity_signals_ranked.sql` | Calculate comparison rates, estimated progression gaps and ranks. |

After running query 03:

1. Export its results as `ga4_dashboard_sessions_v2.csv`.
2. Load the results into the BigQuery table:
   `testcompass-510816.testcompass_analytics.ga4_dashboard_sessions_v2`.
3. Run query 04 to create the opportunity preparation table. This query uses `CREATE OR REPLACE TABLE` and replaces that output table if it already exists.
4. Run query 05 to inspect the preparation counts.
5. Run query 06 and export its results as `ga4_dashboard_test_opportunity_candidates.csv`.

Queries 04–06 reference my BigQuery project. Replace the project and dataset identifiers to reproduce the workflow elsewhere. When loading the session export, check the inferred schema and preserve visitor and session identifiers as strings.

Save the CSV exports in `data/raw/ga4/`.

The earlier notebook sections also read `ga4_session_features.csv` and the initial `ga4_dashboard_sessions.csv`. These represent earlier exports and should not be replaced with the final version under the same filenames.

### Python analysis

The notebook uses Python with pandas and plotting libraries. Open `notebooks/01_ga4_eda.ipynb`, review its file paths and run the relevant sections after creating the required exports.

The initial dashboard validation checks the 23-column export. The final dashboard validation checks `ga4_dashboard_sessions_v2.csv`, which contains 35 columns.

### Tableau

Open `tableau/TestCompass_Tableau_dashboard.twbx` in Tableau. Check the dashboard's data connections and filter behaviour before presenting.

### Streamlit

From the project root, in an environment with Streamlit installed:

```bash
streamlit run streamlit_app/app.py
```

Use the address printed by Streamlit. Tableau URL actions must use the same address and port.

## Presentation

**Google Slides viewing link: https://docs.google.com/presentation/d/1CVjiD3TiH3caKFQgVoYU5XEv9o8XW4Fv/edit?usp=sharing&ouid=112500422231521960830&rtpof=true&sd=true ** 

## Recommended next steps

1. Validate acquisition and cross-domain tracking using business-owned data.
2. Review the landing pages associated with the highest-ranked signal.
3. Use page inspection or user research to develop a specific intervention.
4. Define the experiment audience, success metric and guardrails.
5. Plan sample size and duration before running a randomised test.
6. Evaluate experiment results and record the learning.
7. Add validated transaction revenue when reliable order identifiers are available.

  
