-- One immutable service-run snapshot. Unknown is not zero.
CREATE TEMP VIEW poll AS
SELECT *,
  lag(seq) OVER (ORDER BY seq) AS previous_seq,
  lag(now) OVER (ORDER BY seq) AS previous_now,
  lag(epoch) OVER (ORDER BY seq) AS previous_epoch,
  lag(dispatch) OVER (ORDER BY seq) AS previous_dispatch,
  (ok=1 AND ordered=1 AND epoch=poll_epoch AND begin_ms>0 AND begin_ms<=end_ms AND end_ms<=now AND now-begin_ms<=2000) AS fresh,
  (ta BETWEEN 1 AND 127 AND ra=1) AS valid_ta,
  (tb BETWEEN 1 AND 127 AND rb=1) AS valid_tb,
  (rpm_a BETWEEN 0 AND 8191 AND lo_a=1 AND hi_a=1) AS valid_a,
  (rpm_b BETWEEN 0 AND 8191 AND lo_b=1 AND hi_b=1) AS valid_b
FROM read_csv(__POLL_CSV__, header=true, all_varchar=false, sample_size=-1);
CREATE TEMP VIEW assessed AS
SELECT *, CASE
  WHEN NOT fresh THEN 'stale'
  WHEN NOT(valid_a OR valid_b) THEN 'unknown'
  WHEN valid_a AND valid_b AND (abs(rpm_a-rpm_b)>200 OR ((rpm_a=0)<>(rpm_b=0))) THEN 'disagree'
  WHEN valid_a AND valid_b THEN 'dual'
  ELSE 'single' END AS tach_quality,
  CASE WHEN fresh AND valid_ta AND valid_tb AND abs(ta-tb)<=5 THEN true ELSE false END AS thermal_permit
FROM poll;
CREATE TEMP VIEW gated AS
SELECT *, thermal_permit AND tach_quality='dual' AND rpm_b>0 AS joint_permit,
  previous_seq IS NOT NULL AND seq=previous_seq+1 AND now>previous_now AND now-previous_now<=2000 AND epoch=previous_epoch AS contiguous
FROM assessed;
SELECT count(*) AS polls, min(seq) AS first_seq, max(seq) AS last_seq,
  max(seq)-min(seq)+1-count(*) AS missing_between,
  count_if(previous_seq IS NOT NULL AND NOT contiguous) AS discontinuities,
  count_if(ok=0) AS failed,
  count_if(thermal_permit) AS thermal_permitted,
  count_if(joint_permit) AS joint_permitted,
  round(median(now-begin_ms) FILTER (WHERE begin_ms>0),1) AS acquisition_median_ms,
  max(now-begin_ms) FILTER (WHERE begin_ms>0) AS acquisition_max_ms,
  round(median(now-previous_now) FILTER (WHERE contiguous),1) AS contiguous_median_ms
FROM gated;
SELECT tach_quality,count(*) AS polls FROM gated GROUP BY tach_quality ORDER BY tach_quality;
WITH runs AS (
 SELECT *, sum(CASE WHEN NOT coalesce(contiguous,false) OR NOT joint_permit THEN 1 ELSE 0 END)
 OVER (ORDER BY seq ROWS UNBOUNDED PRECEDING) AS run FROM gated
), eligible AS (
 SELECT run,count(*) AS n,max(now)-min(now) AS duration_ms FROM runs WHERE joint_permit GROUP BY run
)
SELECT coalesce(max(duration_ms),0) AS longest_joint_window_ms,coalesce(max(n),0) AS longest_joint_window_polls FROM eligible;
