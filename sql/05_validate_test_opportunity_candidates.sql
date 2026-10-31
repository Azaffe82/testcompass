SELECT
  segment_dimension,
  step_name,
  COUNT(DISTINCT session_key) AS eligible_sessions,
  COUNT(DISTINCT IF(progressed_flag = 1, session_key, NULL))
    AS progressed_sessions
FROM `testcompass-510816.testcompass_analytics.test_opportunity_candidates`
GROUP BY segment_dimension, step_name
ORDER BY segment_dimension, step_name;