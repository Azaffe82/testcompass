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
-- Step 5: Inspect device and first-user acquisition fields.
-- First-user source is not current-session attribution.
SELECT device.category AS device_category,
 traffic_source.source AS first_user_source,
 traffic_source.medium AS first_user_medium,
 COUNT(*) AS session_start_events,
 COUNT(DISTINCT user_pseudo_id) AS visitors
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
 AND event_name = 'session_start'
GROUP BY 1,2,3 ORDER BY session_start_events DESC;

-- Step 6: Device consistency and session conversion.
WITH events AS (
 SELECT user_pseudo_id, device.category AS device_category, event_name,
 (SELECT MAX(value.int_value) FROM UNNEST(event_params)
 WHERE key = 'ga_session_id') AS session_id
 FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
 WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
), sessions AS (
 SELECT user_pseudo_id, session_id,
 CASE WHEN COUNT(DISTINCT device_category)=1 THEN MAX(device_category)
 WHEN COUNT(DISTINCT device_category)=0 THEN 'missing' ELSE 'mixed' END AS device_category,
 MAX(IF(event_name='purchase',1,0)) AS purchased
 FROM events WHERE session_id IS NOT NULL GROUP BY user_pseudo_id,session_id
)
SELECT device_category, COUNT(*) AS sessions, SUM(purchased) AS purchasing_sessions,
 ROUND(100*AVG(purchased),2) AS conversion_rate_pct
FROM sessions GROUP BY device_category ORDER BY sessions DESC;

-- Step 7: Events strictly preceding first purchase.
-- Missing funnel steps do not prove invalid purchases.
WITH events AS (
 SELECT user_pseudo_id,event_name,event_timestamp,
 (SELECT MAX(value.int_value) FROM UNNEST(event_params)
 WHERE key='ga_session_id') AS session_id
 FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
 WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
), marked AS (
 SELECT *, MIN(IF(event_name='purchase',event_timestamp,NULL))
 OVER(PARTITION BY user_pseudo_id,session_id) AS first_purchase_ts
 FROM events WHERE session_id IS NOT NULL
), journeys AS (
 SELECT user_pseudo_id,session_id,
 COUNTIF(event_name='view_item' AND event_timestamp<first_purchase_ts)>0 AS viewed_before_purchase,
 COUNTIF(event_name='add_to_cart' AND event_timestamp<first_purchase_ts)>0 AS cart_before_purchase,
 COUNTIF(event_name='begin_checkout' AND event_timestamp<first_purchase_ts)>0 AS checkout_before_purchase
 FROM marked WHERE first_purchase_ts IS NOT NULL GROUP BY user_pseudo_id,session_id
)
SELECT COUNT(*) AS purchasing_sessions,
 COUNTIF(viewed_before_purchase) AS with_prior_product_view,
 COUNTIF(cart_before_purchase) AS with_prior_cart,
 COUNTIF(checkout_before_purchase) AS with_prior_checkout,
 COUNTIF(NOT viewed_before_purchase AND NOT cart_before_purchase
 AND NOT checkout_before_purchase) AS without_any_prior_funnel_step
FROM journeys;

-- Step 8: Validate first-product-view prediction population.
WITH events AS (
 SELECT user_pseudo_id,event_name,event_timestamp,
 (SELECT MAX(value.int_value) FROM UNNEST(event_params)
 WHERE key='ga_session_id') AS session_id
 FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
 WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
), sessions AS (
 SELECT user_pseudo_id,session_id,
 MIN(IF(event_name='view_item',event_timestamp,NULL)) AS first_view_ts,
 MIN(IF(event_name='purchase',event_timestamp,NULL)) AS first_purchase_ts
 FROM events WHERE session_id IS NOT NULL GROUP BY user_pseudo_id,session_id
)
SELECT COUNT(*) AS total_sessions,
 COUNTIF(first_view_ts IS NOT NULL) AS sessions_with_product_view,
 COUNTIF(first_view_ts IS NOT NULL AND
 (first_purchase_ts IS NULL OR first_purchase_ts>first_view_ts)) AS eligible_sessions,
 COUNTIF(first_view_ts IS NOT NULL AND first_purchase_ts>first_view_ts) AS eligible_purchasing_sessions,
 COUNTIF(first_view_ts IS NOT NULL AND first_purchase_ts<=first_view_ts) AS excluded_purchase_before_or_at_view
FROM sessions;

-- Observed audit results:
-- 4,295,584 events; 360,129 visitor/session pairs; no missing session IDs.
-- 906 purchase events lack valid transaction IDs; repeated IDs also span visitors.
-- All 92 dates present; session purchase rate approximately 1.35%.
-- Acquisition values partly obscured; no identifiable email/Meta traffic in step 5.
-- 76,995 eligible product-view sessions; 4,673 later purchases (6.07%).
-- Dataset remains provisional: investigate anomalous session timing and boundaries.
