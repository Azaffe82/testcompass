WITH segment_rates AS (
  SELECT
    segment_dimension,
    segment_value,
    category_status,
    step_name,
    COUNT(DISTINCT session_key) AS eligible_sessions,
    COUNT(DISTINCT IF(progressed_flag = 1, session_key, NULL))
      AS progressed_sessions,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(progressed_flag = 1, session_key, NULL)),
      COUNT(DISTINCT session_key)
    ) AS step_rate
  FROM `testcompass-510816.testcompass_analytics.test_opportunity_candidates`
  WHERE category_status = 'Named value'
  GROUP BY segment_dimension, segment_value, category_status, step_name
),

with_comparison AS (
  SELECT
    a.segment_dimension,
    a.segment_value,
    a.category_status,
    a.step_name,
    a.eligible_sessions,
    a.progressed_sessions,
    a.step_rate,
    SAFE_DIVIDE(SUM(b.progressed_sessions), SUM(b.eligible_sessions))
      AS comparison_rate
  FROM segment_rates a
  JOIN segment_rates b
    ON a.segment_dimension = b.segment_dimension
   AND a.step_name = b.step_name
   AND a.segment_value != b.segment_value
  GROUP BY
    a.segment_dimension,
    a.segment_value,
    a.category_status,
    a.step_name,
    a.eligible_sessions,
    a.progressed_sessions,
    a.step_rate
),

scored AS (
  SELECT
    *,
    comparison_rate - step_rate AS rate_gap,
    GREATEST(comparison_rate - step_rate, 0) * eligible_sessions
      AS estimated_progression_gap
  FROM with_comparison
)

SELECT
  *,
  RANK() OVER (ORDER BY estimated_progression_gap DESC) AS opportunity_rank
FROM scored
ORDER BY opportunity_rank;