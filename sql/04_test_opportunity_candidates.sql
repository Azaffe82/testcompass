CREATE OR REPLACE TABLE
  `testcompass-510816.testcompass_analytics.test_opportunity_candidates` AS

WITH base AS (
  SELECT
    SAFE_CAST(session_date AS DATE) AS session_date,
    CAST(session_id AS STRING) AS session_id,
    CAST(user_pseudo_id AS STRING) AS user_pseudo_id,
    CAST(device_category AS STRING) AS device_category,
    CAST(first_user_medium AS STRING) AS first_user_medium,
    CAST(first_user_source AS STRING) AS first_user_source,

    COALESCE(SAFE_CAST(reached_product_view AS INT64), 0)
      AS reached_product_view,
    COALESCE(SAFE_CAST(reached_cart_after_view AS INT64), 0)
      AS reached_cart_after_view,
    COALESCE(SAFE_CAST(reached_checkout_after_cart AS INT64), 0)
      AS reached_checkout_after_cart,
    COALESCE(SAFE_CAST(reached_purchase_after_checkout AS INT64), 0)
      AS reached_purchase_after_checkout
  FROM `testcompass-510816.testcompass_analytics.ga4_dashboard_sessions_v2`
  WHERE session_id IS NOT NULL
),

expanded AS (
  SELECT
    b.session_date,
    CONCAT(COALESCE(b.user_pseudo_id, ''), '|', b.session_id) AS session_key,
    b.device_category,
    b.first_user_medium,
    b.first_user_source,
    segment.segment_dimension,
    segment.segment_value,
    step.step_name,
    step.progressed_flag
  FROM base AS b

  CROSS JOIN UNNEST([
    STRUCT('Device Category' AS segment_dimension,
           b.device_category AS segment_value),
    STRUCT('First User Medium' AS segment_dimension,
           b.first_user_medium AS segment_value),
    STRUCT('First User Source' AS segment_dimension,
           b.first_user_source AS segment_value)
  ]) AS segment

  CROSS JOIN UNNEST([
    STRUCT('Sessions to Product View' AS step_name,
           1 AS eligible_flag,
           b.reached_product_view AS progressed_flag),
    STRUCT('Product View to Add to Cart' AS step_name,
           b.reached_product_view AS eligible_flag,
           b.reached_cart_after_view AS progressed_flag),
    STRUCT('Add to Cart to Begin Checkout' AS step_name,
           b.reached_cart_after_view AS eligible_flag,
           b.reached_checkout_after_cart AS progressed_flag),
    STRUCT('Begin Checkout to Purchase' AS step_name,
           b.reached_checkout_after_cart AS eligible_flag,
           b.reached_purchase_after_checkout AS progressed_flag)
  ]) AS step

  WHERE step.eligible_flag = 1
)

SELECT
  *,
  CASE
    WHEN segment_value IS NULL OR TRIM(segment_value) = ''
      THEN 'Missing'
    WHEN LOWER(TRIM(segment_value)) IN
         ('(data deleted)', '<other>', '(none)', '(not set)')
      THEN 'Unclear attribution'
    ELSE 'Named value'
  END AS category_status
FROM expanded;
