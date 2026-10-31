-- Step 1: Initial data audit
-- Inspect event types, event counts and unique visitors per event.
-- Check for missing visitor IDs and confirm purchase events exist.
-- Dataset period: 2020-11-01 to 2021-01-31.

SELECT
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNTIF(user_pseudo_id IS NULL) AS missing_user_ids
FROM
  `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_name
ORDER BY event_count DESC;


-- Step 2: Session and transaction identifier checks
-- Measure missing session IDs and count distinct visitor-session pairs.
-- Compare purchase events with distinct transaction IDs.
-- Flag missing or placeholder transaction IDs.

WITH events AS (
  SELECT
    user_pseudo_id,
    event_name,
    ecommerce.transaction_id AS transaction_id,
    (
      SELECT MAX(value.int_value)
      FROM UNNEST(event_params)
      WHERE key = 'ga_session_id'
    ) AS session_id
  FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
)
SELECT
  COUNT(*) AS total_events,
  COUNTIF(session_id IS NULL) AS events_missing_session_id,
  COUNT(DISTINCT IF(
    session_id IS NOT NULL,
    CONCAT(user_pseudo_id, '.', CAST(session_id AS STRING)),
    NULL
  )) AS distinct_sessions,
  COUNTIF(event_name = 'purchase') AS purchase_events,
  COUNTIF(
    event_name = 'purchase'
    AND (
      transaction_id IS NULL
      OR TRIM(transaction_id) IN ('', '(not set)', '<Other>')
    )
  ) AS purchases_without_valid_transaction_id,
  COUNT(DISTINCT IF(
    event_name = 'purchase'
    AND TRIM(transaction_id) NOT IN ('', '(not set)', '<Other>'),
    transaction_id,
    NULL
  )) AS distinct_transaction_ids
FROM events;


-- Step 3: Investigate repeated purchase transaction IDs
-- Check whether repeated IDs span different visitors or sessions.

WITH purchases AS (
  SELECT
    user_pseudo_id,
    ecommerce.transaction_id AS transaction_id,
    (
      SELECT MAX(value.int_value)
      FROM UNNEST(event_params)
      WHERE key = 'ga_session_id'
    ) AS session_id
  FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'purchase'
)
SELECT
  transaction_id,
  COUNT(*) AS purchase_events,
  COUNT(DISTINCT user_pseudo_id) AS visitors,
  COUNT(DISTINCT CONCAT(
    user_pseudo_id, '.', CAST(session_id AS STRING)
  )) AS sessions
FROM purchases
WHERE TRIM(transaction_id) NOT IN ('', '(not set)', '<Other>')
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY purchase_events DESC;

-- : Repeated transaction IDs occur within sessions
-- and across different visitors.
-- Transaction ID alone is not a reliable global deduplication key.
-- For conversion analysis, count each purchasing session once.


-- Step 4: Check daily coverage and session conversion patterns
WITH events AS (
  SELECT
    event_date,
    user_pseudo_id,
    event_name,
    (
      SELECT MAX(value.int_value)
      FROM UNNEST(event_params)
      WHERE key = 'ga_session_id'
    ) AS session_id
  FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),
sessions AS (
  SELECT
    user_pseudo_id,
    session_id,
    MIN(event_date) AS session_date,
    MAX(IF(event_name = 'purchase', 1, 0)) AS purchased
  FROM events
  WHERE session_id IS NOT NULL
  GROUP BY user_pseudo_id, session_id
)
SELECT
  session_date,
  COUNT(*) AS sessions,
  SUM(purchased) AS purchasing_sessions,
  ROUND(100 * AVG(purchased), 2) AS conversion_rate_pct
FROM sessions
GROUP BY session_date
ORDER BY session_date;