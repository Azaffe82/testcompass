-- One row per eligible product-view session.
-- Predict purchase after the first product view.
-- Behaviour features use strictly earlier events; context uses first view.
-- IDs are audit keys, not model features.
-- This reconstructs the query used for the existing 76,995-row CSV.
-- Timing outliers and dataset boundary censoring still require investigation.
WITH events AS (
 SELECT user_pseudo_id,event_name,event_timestamp,event_date,
 device.category AS device_category,
 traffic_source.source AS first_user_source,
 traffic_source.medium AS first_user_medium,
 (SELECT MAX(value.int_value) FROM UNNEST(event_params)
 WHERE key='ga_session_id') AS session_id
 FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
 WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
), session_bounds AS (
 SELECT user_pseudo_id,session_id,
 MIN(event_timestamp) AS first_observed_ts,
 MIN(IF(event_name='view_item',event_timestamp,NULL)) AS first_view_ts,
 MIN(IF(event_name='purchase',event_timestamp,NULL)) AS first_purchase_ts
 FROM events WHERE session_id IS NOT NULL GROUP BY user_pseudo_id,session_id
), eligible AS (
 SELECT * FROM session_bounds WHERE first_view_ts IS NOT NULL
 AND (first_purchase_ts IS NULL OR first_purchase_ts>first_view_ts)
), view_context AS (
 SELECT e.user_pseudo_id,e.session_id,
 ARRAY_AGG(STRUCT(e.event_date AS prediction_date,
 e.device_category AS device_category,e.first_user_source AS first_user_source,
 e.first_user_medium AS first_user_medium)
 ORDER BY e.event_date,e.device_category,e.first_user_source,e.first_user_medium
 LIMIT 1)[OFFSET(0)] AS context
 FROM events e JOIN eligible s USING(user_pseudo_id,session_id)
 WHERE e.event_name='view_item' AND e.event_timestamp=s.first_view_ts
 GROUP BY e.user_pseudo_id,e.session_id
), prior_behaviour AS (
 SELECT s.user_pseudo_id,s.session_id,
 COUNTIF(e.event_timestamp<s.first_view_ts) AS prior_events,
 COUNTIF(e.event_timestamp<s.first_view_ts AND e.event_name='page_view') AS prior_page_views,
 COUNTIF(e.event_timestamp<s.first_view_ts AND e.event_name='view_search_results') AS prior_search_events,
 COUNTIF(e.event_timestamp<s.first_view_ts AND e.event_name='add_to_cart') AS prior_cart_events,
 COUNTIF(e.event_timestamp<s.first_view_ts AND e.event_name='first_visit') AS prior_first_visit_events
 FROM eligible s JOIN events e USING(user_pseudo_id,session_id)
 GROUP BY s.user_pseudo_id,s.session_id
)
SELECT s.user_pseudo_id,s.session_id,
 PARSE_DATE('%Y%m%d',v.context.prediction_date) AS prediction_date,
 TIMESTAMP_MICROS(s.first_view_ts) AS prediction_timestamp,
 v.context.device_category,v.context.first_user_source,v.context.first_user_medium,
 (s.first_view_ts-s.first_observed_ts)/1000000.0 AS seconds_before_first_view,
 p.prior_events,p.prior_page_views,p.prior_search_events,p.prior_cart_events,
 p.prior_first_visit_events,
 IF(s.first_purchase_ts>s.first_view_ts,1,0) AS purchased_later
FROM eligible s JOIN view_context v USING(user_pseudo_id,session_id)
JOIN prior_behaviour p USING(user_pseudo_id,session_id)
ORDER BY prediction_timestamp,user_pseudo_id,session_id;
