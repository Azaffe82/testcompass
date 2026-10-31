-- UPDATED DASHBOARD EXPORT: original 23 columns + 12 new columns = 35.
-- Read-only SELECT: does not replace/create any BigQuery table.
-- Strict same-session funnel: product view -> cart -> checkout -> purchase.
-- Each later step must have a strictly greater timestamp than the prior step.
-- Greedy earliest qualifying timestamps identify any valid full sequence.
-- Equal timestamps are not ordered; skipped stages do not enter later steps.
-- This is session-level, not item-level; stages can involve different products.
-- Missing steps may reflect behavior, obfuscation or measurement limitations.
-- Original purchased remains ALL purchasing sessions. Do not substitute the
-- stricter reached_purchase_after_checkout into the overall purchase-rate KPI.
-- Preserve user/session IDs as strings when loading the export into Python.

-- Dashboard dataset: all observed visitor-session pairs
  -- Period: 1 November 2020 to 31 January 2021.
  -- Include sessions with and without product views or purchases.
  -- Existing flags indicate event presence; new reached_* flags use strict order.
  -- First-user acquisition is not current-session attribution.
  -- Retain timing anomalies and expose them as audit flags.
  -- Duration measures observed elapsed time, not active engagement.
  -- Sessions at dataset boundaries may be incomplete.

WITH events AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date,
    device.category AS device_category,
    traffic_source.source AS first_user_source,
    traffic_source.medium AS first_user_medium,
    (
      SELECT MAX(value.int_value)
      FROM UNNEST(event_params)
      WHERE key = 'ga_session_id'
    ) AS session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),
ordered_events AS (
  SELECT
    *,
    (
      event_timestamp - LAG(event_timestamp) OVER (
        PARTITION BY user_pseudo_id, session_id
        ORDER BY event_timestamp
      )
    ) / 1000000.0 AS gap_seconds
  FROM events
  WHERE user_pseudo_id IS NOT NULL
    AND session_id IS NOT NULL
),
sessions AS (
  SELECT
    user_pseudo_id,
    session_id,
    MIN(event_date) AS session_date,
    MIN(event_timestamp) AS first_event_ts,
    MAX(event_timestamp) AS last_event_ts,
    CASE
      WHEN COUNT(DISTINCT device_category) = 0 THEN 'missing'
      WHEN COUNT(DISTINCT device_category) = 1
        THEN MAX(device_category)
      ELSE 'mixed'
    END AS device_category,
    ARRAY_AGG(
      STRUCT(
        first_user_source AS source,
        first_user_medium AS medium
      )
      ORDER BY
        event_timestamp,
        first_user_source,
        first_user_medium
      LIMIT 1
    )[OFFSET(0)] AS acquisition,
    COUNT(*) AS event_count,
    COUNTIF(event_name = 'page_view') AS page_views,
    COUNTIF(event_name = 'view_item') AS product_views,
    COUNTIF(event_name = 'add_to_cart') AS cart_events,
    COUNTIF(event_name = 'begin_checkout') AS checkout_events,
    COUNTIF(event_name = 'purchase') AS purchase_events,
    COUNTIF(event_name = 'session_start') AS session_start_events,
    COUNTIF(event_name = 'first_visit') AS first_visit_events,
    MAX(gap_seconds) AS max_gap_seconds,
    MIN(IF(event_name = 'view_item', event_timestamp, NULL)) AS first_product_view_ts
  FROM ordered_events
  GROUP BY user_pseudo_id, session_id
),
cart_steps AS (
  SELECT
    s.user_pseudo_id,
    s.session_id,
    MIN(e.event_timestamp) AS cart_after_view_ts
  FROM sessions s
  LEFT JOIN ordered_events e
    ON s.user_pseudo_id = e.user_pseudo_id
    AND s.session_id = e.session_id
    AND e.event_name = 'add_to_cart'
    AND e.event_timestamp > s.first_product_view_ts
  GROUP BY s.user_pseudo_id, s.session_id
),
checkout_steps AS (
  SELECT
    c.user_pseudo_id,
    c.session_id,
    c.cart_after_view_ts,
    MIN(e.event_timestamp) AS checkout_after_cart_ts
  FROM cart_steps c
  LEFT JOIN ordered_events e
    ON c.user_pseudo_id = e.user_pseudo_id
    AND c.session_id = e.session_id
    AND e.event_name = 'begin_checkout'
    AND e.event_timestamp > c.cart_after_view_ts
  GROUP BY c.user_pseudo_id, c.session_id, c.cart_after_view_ts
),
purchase_steps AS (
  SELECT
    c.user_pseudo_id,
    c.session_id,
    c.cart_after_view_ts,
    c.checkout_after_cart_ts,
    MIN(e.event_timestamp) AS purchase_after_checkout_ts
  FROM checkout_steps c
  LEFT JOIN ordered_events e
    ON c.user_pseudo_id = e.user_pseudo_id
    AND c.session_id = e.session_id
    AND e.event_name = 'purchase'
    AND e.event_timestamp > c.checkout_after_cart_ts
  GROUP BY c.user_pseudo_id, c.session_id,
    c.cart_after_view_ts, c.checkout_after_cart_ts
),
dashboard_base AS (
SELECT
  user_pseudo_id,
  session_id,
  PARSE_DATE('%Y%m%d', session_date) AS session_date,
  TIMESTAMP_MICROS(first_event_ts) AS first_observed_time,
  TIMESTAMP_MICROS(last_event_ts) AS last_observed_time,
  device_category,
  acquisition.source AS first_user_source,
  acquisition.medium AS first_user_medium,
  event_count,
  page_views,
  product_views,
  cart_events,
  checkout_events,
  purchase_events,
  session_start_events,
  first_visit_events,
  IF(product_views > 0, 1, 0) AS viewed_product,
  IF(cart_events > 0, 1, 0) AS added_to_cart,
  IF(checkout_events > 0, 1, 0) AS began_checkout,
  IF(purchase_events > 0, 1, 0) AS purchased,
  (last_event_ts - first_event_ts) / 1000000.0
    AS observed_duration_seconds,
  COALESCE(max_gap_seconds, 0) AS max_event_gap_seconds,
  IF(COALESCE(max_gap_seconds, 0) > 1800, 1, 0)
    AS has_gap_over_30min
FROM sessions
)
-- Preserve every original column, in its original order, before new fields.
SELECT
  b.*,
  TIMESTAMP_MICROS(s.first_product_view_ts) AS funnel_first_product_view_time,
  TIMESTAMP_MICROS(p.cart_after_view_ts) AS funnel_cart_after_view_time,
  TIMESTAMP_MICROS(p.checkout_after_cart_ts) AS funnel_checkout_after_cart_time,
  TIMESTAMP_MICROS(p.purchase_after_checkout_ts) AS funnel_purchase_after_checkout_time,
  IF(s.first_product_view_ts IS NOT NULL, 1, 0) AS reached_product_view,
  IF(p.cart_after_view_ts IS NOT NULL, 1, 0) AS reached_cart_after_view,
  IF(p.checkout_after_cart_ts IS NOT NULL, 1, 0) AS reached_checkout_after_cart,
  IF(p.purchase_after_checkout_ts IS NOT NULL, 1, 0) AS reached_purchase_after_checkout,
  -- Co-occurrence audit flags: these do NOT establish event order or tag failure.
  IF(b.began_checkout = 1 AND b.added_to_cart = 0, 1, 0)
    AS checkout_without_cart_event,
  IF(b.purchased = 1 AND b.began_checkout = 0, 1, 0)
    AS purchase_without_checkout_event,
  IF(b.session_start_events = 0, 1, 0) AS missing_session_start_event,
  IF(
    b.first_user_source IS NULL
    OR TRIM(b.first_user_source) IN ('', '(not set)', '<Other>'),
    1, 0
  ) AS obscured_or_missing_first_user_source
FROM dashboard_base b
LEFT JOIN sessions s USING (user_pseudo_id, session_id)
LEFT JOIN purchase_steps p USING (user_pseudo_id, session_id)
ORDER BY b.session_date, b.user_pseudo_id, b.session_id;
