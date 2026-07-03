#!/usr/bin/env python3
"""Generate TT biweekly attribution dashboard from sandbox benchmark + Moloco details."""

from __future__ import annotations

import csv
import html
import subprocess
from collections import defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path


REPO_DIR = Path("/Users/zoey.wang/Desktop/tt-report")
OUTPUT_FILE = REPO_DIR / "biweekly.html"

PROJECT = "ads-bpd-guard-sandbox"
CURR_START = "2026-06-15"
CURR_END = "2026-06-28"
PREV_START = "2026-06-01"
PREV_END = "2026-06-14"
MAX_DETAIL_SEGMENTS = 20


def run_bq(sql: str, max_rows: int = 20000) -> list[dict[str, str]]:
    cmd = [
        "bq",
        "query",
        f"--project_id={PROJECT}",
        "--use_legacy_sql=false",
        "--format=csv",
        f"--max_rows={max_rows}",
        sql,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)
    text = res.stdout.strip()
    if not text:
        return []
    return list(csv.DictReader(StringIO(text)))


def fnum(v, default=0.0) -> float:
    if v in (None, "", "NULL", "nan"):
        return default
    try:
        return float(v)
    except Exception:
        return default


def pct(v) -> str:
    if v in (None, ""):
        return "-"
    x = fnum(v)
    sign = "+" if x > 0 else ""
    return f"{sign}{x:.1f}%"


def money(v) -> str:
    x = fnum(v)
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.2f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:.1f}K"
    return f"${x:.0f}"


def num(v) -> str:
    x = fnum(v)
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if abs(x) >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{x:.0f}"


def cpi(v) -> str:
    return f"${fnum(v):.2f}"


def cls_change(v) -> str:
    x = fnum(v)
    if x >= 10:
        return "up"
    if x <= -10:
        return "down"
    return "flat"


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def period_case(date_col: str) -> str:
    return (
        f"CASE WHEN {date_col} BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'current' "
        f"WHEN {date_col} BETWEEN '{PREV_START}' AND '{PREV_END}' THEN 'previous' END"
    )


BENCHMARK_SQL = f"""
WITH region_src AS (
  SELECT
    'Android' AS os,
    CAST(app_id AS STRING) AS app_id,
    region,
    p_date,
    spend,
    dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_android_region_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
  UNION ALL
  SELECT
    'iOS' AS os,
    CAST(app_id AS STRING) AS app_id,
    region,
    p_date,
    rebate_cost_daily_avg AS spend,
    bs_ios_dc_new_user_daily_avg AS dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_ios_region_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
),
agg AS (
  SELECT
    {period_case("p_date")} AS period_tag,
    os,
    app_id,
    region,
    SUM(spend) AS spend,
    SUM(dnu) AS dnu
  FROM region_src
  WHERE spend IS NOT NULL OR dnu IS NOT NULL
  GROUP BY 1,2,3,4
),
pivoted AS (
  SELECT
    os,
    app_id,
    region,
    SUM(IF(period_tag='previous', spend, 0)) AS prev_spend,
    SUM(IF(period_tag='current', spend, 0)) AS curr_spend,
    SUM(IF(period_tag='previous', dnu, 0)) AS prev_dnu,
    SUM(IF(period_tag='current', dnu, 0)) AS curr_dnu
  FROM agg
  WHERE period_tag IS NOT NULL
  GROUP BY 1,2,3
),
scored AS (
  SELECT
    CONCAT(region, '|', os, '|', app_id) AS segment_key,
    region,
    os,
    app_id,
    prev_spend,
    curr_spend,
    prev_dnu,
    curr_dnu,
    SAFE_DIVIDE(prev_spend, NULLIF(prev_dnu, 0)) AS prev_cpi,
    SAFE_DIVIDE(curr_spend, NULLIF(curr_dnu, 0)) AS curr_cpi,
    (SAFE_DIVIDE(SAFE_DIVIDE(curr_spend, NULLIF(curr_dnu, 0)), NULLIF(SAFE_DIVIDE(prev_spend, NULLIF(prev_dnu, 0)), 0)) - 1) * 100 AS cpi_chg_pct,
    (SAFE_DIVIDE(curr_dnu, NULLIF(prev_dnu, 0)) - 1) * 100 AS dnu_chg_pct
  FROM pivoted
  WHERE prev_spend >= 100
    AND curr_spend >= 100
    AND prev_dnu > 0
    AND curr_dnu > 0
),
flagged AS (
  SELECT
    *,
    CASE
      WHEN ABS(cpi_chg_pct) >= 10 AND ABS(dnu_chg_pct) >= 10 THEN 'CPI & DNU'
      WHEN ABS(cpi_chg_pct) >= 10 THEN 'CPI'
      ELSE 'DNU'
    END AS trigger_metric,
    CASE
      WHEN cpi_chg_pct >= 10 THEN 'CPI上升'
      WHEN cpi_chg_pct <= -10 THEN 'CPI下降'
      WHEN dnu_chg_pct >= 10 THEN 'DNU上升'
      ELSE 'DNU下降'
    END AS direction
  FROM scored
  WHERE ABS(cpi_chg_pct) >= 10 OR ABS(dnu_chg_pct) >= 10
)
SELECT
  segment_key,
  region,
  os,
  app_id,
  ROUND(prev_spend, 2) AS prev_spend,
  ROUND(curr_spend, 2) AS curr_spend,
  ROUND(prev_dnu, 2) AS prev_dnu,
  ROUND(curr_dnu, 2) AS curr_dnu,
  ROUND(prev_cpi, 4) AS prev_cpi,
  ROUND(curr_cpi, 4) AS curr_cpi,
  ROUND(cpi_chg_pct, 1) AS cpi_chg_pct,
  ROUND(dnu_chg_pct, 1) AS dnu_chg_pct,
  trigger_metric,
  direction
FROM flagged
ORDER BY curr_spend DESC, ABS(cpi_chg_pct) DESC
"""


def flags_cte(limit: int = MAX_DETAIL_SEGMENTS) -> str:
    return f"""
WITH region_src AS (
  SELECT 'Android' AS os, CAST(app_id AS STRING) AS app_id, region, p_date, spend, dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_android_region_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
  UNION ALL
  SELECT 'iOS' AS os, CAST(app_id AS STRING) AS app_id, region, p_date,
         rebate_cost_daily_avg AS spend, bs_ios_dc_new_user_daily_avg AS dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_ios_region_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
),
region_agg AS (
  SELECT {period_case("p_date")} AS period_tag, os, app_id, region,
         SUM(spend) AS spend, SUM(dnu) AS dnu
  FROM region_src
  GROUP BY 1,2,3,4
),
region_pivot AS (
  SELECT os, app_id, region,
         SUM(IF(period_tag='previous', spend, 0)) AS prev_spend,
         SUM(IF(period_tag='current', spend, 0)) AS curr_spend,
         SUM(IF(period_tag='previous', dnu, 0)) AS prev_dnu,
         SUM(IF(period_tag='current', dnu, 0)) AS curr_dnu
  FROM region_agg
  WHERE period_tag IS NOT NULL
  GROUP BY 1,2,3
),
flagged_all AS (
  SELECT
    CONCAT(region, '|', os, '|', app_id) AS segment_key,
    region, os, app_id,
    prev_spend, curr_spend, prev_dnu, curr_dnu,
    SAFE_DIVIDE(prev_spend, NULLIF(prev_dnu, 0)) AS prev_cpi,
    SAFE_DIVIDE(curr_spend, NULLIF(curr_dnu, 0)) AS curr_cpi,
    (SAFE_DIVIDE(SAFE_DIVIDE(curr_spend, NULLIF(curr_dnu, 0)), NULLIF(SAFE_DIVIDE(prev_spend, NULLIF(prev_dnu, 0)), 0)) - 1) * 100 AS cpi_chg_pct,
    (SAFE_DIVIDE(curr_dnu, NULLIF(prev_dnu, 0)) - 1) * 100 AS dnu_chg_pct
  FROM region_pivot
  WHERE prev_spend >= 100
    AND curr_spend >= 100
    AND prev_dnu > 0
    AND curr_dnu > 0
    AND (
      ABS((SAFE_DIVIDE(SAFE_DIVIDE(curr_spend, NULLIF(curr_dnu, 0)), NULLIF(SAFE_DIVIDE(prev_spend, NULLIF(prev_dnu, 0)), 0)) - 1) * 100) >= 10
      OR ABS((SAFE_DIVIDE(curr_dnu, NULLIF(prev_dnu, 0)) - 1) * 100) >= 10
    )
),
top_flags AS (
  SELECT *
  FROM flagged_all
  ORDER BY curr_spend DESC, ABS(cpi_chg_pct) DESC
  LIMIT {limit}
),
campaign_src AS (
  SELECT 'Android' AS os, CAST(app_id AS STRING) AS app_id, region, p_date, campaign_name, spend, dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_android_campaign_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
  UNION ALL
  SELECT 'iOS' AS os, CAST(app_id AS STRING) AS app_id, region, p_date, campaign_name,
         rebate_cost_daily_avg AS spend, bs_ios_dc_new_user_daily_avg AS dnu
  FROM `ads-bpd-guard-sandbox.sherry.tt_ios_campaign_daily`
  WHERE p_date BETWEEN '{PREV_START}' AND '{CURR_END}'
),
campaign_map AS (
  SELECT DISTINCT
    f.segment_key,
    f.region,
    f.os,
    f.app_id,
    c.campaign_name
  FROM top_flags f
  JOIN campaign_src c
  USING (region, os, app_id)
  WHERE c.campaign_name IS NOT NULL
    AND c.campaign_name != ''
    AND IFNULL(c.spend, 0) > 0
)
"""


def detail_sql(kind: str) -> str:
    if kind == "campaign":
        source = "`ads-bpd-guard-china.athena.fact_dsp_core`"
        dim = """
          f.campaign.title AS dim_name,
          COALESCE(f.campaign.payout_event, f.campaign.kpi_actions, 'n/a') AS dim_sub,
          CAST(NULL AS STRING) AS dim_extra
        """
        group_by = "1,2,3,4,5,6,7,8"
    elif kind == "media":
        source = "`ads-bpd-guard-china.athena.fact_dsp_core`"
        dim = """
          f.exchange AS dim_name,
          'exchange' AS dim_sub,
          CAST(NULL AS STRING) AS dim_extra
        """
        group_by = "1,2,3,4,5,6,7,8"
    elif kind == "creative":
        source = "`ads-bpd-guard-china.athena.fact_dsp_creative`"
        dim = """
          COALESCE(f.creative.group_title, f.creative.title, f.creative.id, '(unknown)') AS dim_name,
          COALESCE(f.creative.format, '(unknown)') AS dim_sub,
          COALESCE(f.creative.inventory_format, '(unknown)') AS dim_extra
        """
        group_by = "1,2,3,4,5,6,7,8"
    elif kind == "bundle":
        source = "`ads-bpd-guard-china.athena.fact_dsp_publisher`"
        dim = """
          COALESCE(f.publisher.app_market_bundle, '(unknown)') AS dim_name,
          'bundle' AS dim_sub,
          CAST(NULL AS STRING) AS dim_extra
        """
        group_by = "1,2,3,4,5,6,7,8"
    else:
        raise ValueError(kind)

    return (
        flags_cte()
        + f""",
fact_base AS (
  SELECT
    cm.segment_key,
    cm.region,
    cm.os,
    cm.app_id,
    {period_case("f.date_utc")} AS period_tag,
    {dim},
    SUM(CAST(f.gross_spend_usd AS FLOAT64)) AS spend,
    SUM(f.installs) AS installs,
    SUM(f.impressions) AS impressions,
    SUM(f.clicks) AS clicks
  FROM {source} f
  JOIN campaign_map cm
    ON f.campaign.title = cm.campaign_name
  WHERE f.date_utc BETWEEN '{PREV_START}' AND '{CURR_END}'
  GROUP BY {group_by}
),
metrics AS (
  SELECT
    *,
    SAFE_DIVIDE(spend, NULLIF(installs, 0)) AS cpi,
    SAFE_DIVIDE(spend, NULLIF(impressions, 0)) * 1000 AS cpm,
    SAFE_DIVIDE(installs, NULLIF(impressions, 0)) * 1000 AS ipm
  FROM fact_base
  WHERE period_tag IS NOT NULL
),
pivoted AS (
  SELECT
    segment_key,
    region,
    os,
    app_id,
    dim_name,
    dim_sub,
    dim_extra,
    SUM(IF(period_tag='previous', spend, 0)) AS prev_spend,
    SUM(IF(period_tag='current', spend, 0)) AS curr_spend,
    SUM(IF(period_tag='previous', installs, 0)) AS prev_installs,
    SUM(IF(period_tag='current', installs, 0)) AS curr_installs,
    SUM(IF(period_tag='previous', impressions, 0)) AS prev_impressions,
    SUM(IF(period_tag='current', impressions, 0)) AS curr_impressions,
    SUM(IF(period_tag='previous', clicks, 0)) AS prev_clicks,
    SUM(IF(period_tag='current', clicks, 0)) AS curr_clicks
  FROM metrics
  GROUP BY 1,2,3,4,5,6,7
),
scored AS (
  SELECT
    *,
    SAFE_DIVIDE(prev_spend, NULLIF(prev_installs, 0)) AS prev_cpi,
    SAFE_DIVIDE(curr_spend, NULLIF(curr_installs, 0)) AS curr_cpi,
    SAFE_DIVIDE(prev_spend, NULLIF(prev_impressions, 0)) * 1000 AS prev_cpm,
    SAFE_DIVIDE(curr_spend, NULLIF(curr_impressions, 0)) * 1000 AS curr_cpm,
    SAFE_DIVIDE(prev_installs, NULLIF(prev_impressions, 0)) * 1000 AS prev_ipm,
    SAFE_DIVIDE(curr_installs, NULLIF(curr_impressions, 0)) * 1000 AS curr_ipm
  FROM pivoted
  WHERE curr_spend >= 30 OR prev_spend >= 30
)
SELECT
  '{kind}' AS detail_type,
  segment_key,
  region,
  os,
  app_id,
  dim_name,
  dim_sub,
  dim_extra,
  ROUND(prev_spend, 2) AS prev_spend,
  ROUND(curr_spend, 2) AS curr_spend,
  ROUND(100 * SAFE_DIVIDE(curr_spend, SUM(curr_spend) OVER (PARTITION BY segment_key)), 2) AS curr_share,
  ROUND(100 * (SAFE_DIVIDE(curr_spend, SUM(curr_spend) OVER (PARTITION BY segment_key)) - SAFE_DIVIDE(prev_spend, NULLIF(SUM(prev_spend) OVER (PARTITION BY segment_key), 0))), 2) AS share_chg_pp,
  prev_installs,
  curr_installs,
  ROUND(prev_cpi, 4) AS prev_cpi,
  ROUND(curr_cpi, 4) AS curr_cpi,
  ROUND((SAFE_DIVIDE(curr_cpi, NULLIF(prev_cpi, 0)) - 1) * 100, 1) AS cpi_chg_pct,
  ROUND(prev_cpm, 4) AS prev_cpm,
  ROUND(curr_cpm, 4) AS curr_cpm,
  ROUND((SAFE_DIVIDE(curr_cpm, NULLIF(prev_cpm, 0)) - 1) * 100, 1) AS cpm_chg_pct,
  ROUND(prev_ipm, 4) AS prev_ipm,
  ROUND(curr_ipm, 4) AS curr_ipm,
  ROUND((SAFE_DIVIDE(curr_ipm, NULLIF(prev_ipm, 0)) - 1) * 100, 1) AS ipm_chg_pct
FROM scored
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY segment_key
  ORDER BY curr_spend DESC
) <= 12
ORDER BY segment_key, curr_spend DESC
"""
    )


def load_data():
    benchmark = run_bq(BENCHMARK_SQL, max_rows=5000)
    details = {
        "campaign": run_bq(detail_sql("campaign"), max_rows=10000),
        "media": run_bq(detail_sql("media"), max_rows=10000),
        "creative": run_bq(detail_sql("creative"), max_rows=10000),
        "bundle": run_bq(detail_sql("bundle"), max_rows=10000),
    }
    return benchmark, details


def group_details(details):
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for dtype, rows in details.items():
        for row in rows:
            grouped[row["segment_key"]][dtype].append(row)
    return grouped


def render_overview_rows(flags: list[dict[str, str]]) -> str:
    rows = []
    for r in flags:
        c = cls_change(r["cpi_chg_pct"])
        d = cls_change(r["dnu_chg_pct"])
        rows.append(
            f"""
            <tr>
              <td><strong>{esc(r['region'])}</strong></td>
              <td>{esc(r['os'])}</td>
              <td>{esc(r['app_id'])}</td>
              <td>{esc(r['trigger_metric'])}</td>
              <td>{money(r['curr_spend'])}</td>
              <td>{num(r['curr_dnu'])}</td>
              <td>{cpi(r['prev_cpi'])} → <strong>{cpi(r['curr_cpi'])}</strong></td>
              <td class="{c}">{pct(r['cpi_chg_pct'])}</td>
              <td class="{d}">{pct(r['dnu_chg_pct'])}</td>
              <td><a href="#seg-{esc(r['segment_key']).replace('|','-')}">查看归因</a></td>
            </tr>
            """
        )
    return "\n".join(rows)


def top_driver(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if not rows:
        return None
    return sorted(rows, key=lambda x: fnum(x.get("curr_spend")), reverse=True)[0]


def render_detail_table(rows: list[dict[str, str]], label: str) -> str:
    if not rows:
        return '<div class="empty">Moloco 明细暂无匹配数据</div>'
    trs = []
    for r in rows[:10]:
        name = r["dim_name"]
        sub = r.get("dim_sub") or ""
        extra = r.get("dim_extra") or ""
        subline = " · ".join(x for x in (sub, extra) if x and x != "NULL")
        trs.append(
            f"""
            <tr>
              <td class="name"><strong>{esc(name)}</strong><span>{esc(subline)}</span></td>
              <td>{money(r['curr_spend'])}</td>
              <td>{fnum(r['curr_share']):.1f}%</td>
              <td class="{cls_change(r['share_chg_pp'])}">{fnum(r['share_chg_pp']):+.1f}pp</td>
              <td>{cpi(r['curr_cpi'])}</td>
              <td class="{cls_change(r['cpi_chg_pct'])}">{pct(r['cpi_chg_pct'])}</td>
              <td>{cpi(r['curr_cpm'])}</td>
              <td class="{cls_change(r['cpm_chg_pct'])}">{pct(r['cpm_chg_pct'])}</td>
              <td>{fnum(r['curr_ipm']):.2f}</td>
              <td class="{cls_change(r['ipm_chg_pct'])}">{pct(r['ipm_chg_pct'])}</td>
            </tr>
            """
        )
    return f"""
    <div class="detail-table">
      <h4>{label}</h4>
      <table>
        <thead><tr><th>维度</th><th>本期消耗</th><th>占比</th><th>占比变化</th><th>CPI</th><th>CPI变化</th><th>CPM</th><th>CPM变化</th><th>IPM</th><th>IPM变化</th></tr></thead>
        <tbody>{''.join(trs)}</tbody>
      </table>
    </div>
    """


def render_detail_blocks(flags: list[dict[str, str]], grouped) -> str:
    blocks = []
    top_keys = {r["segment_key"] for r in flags[:MAX_DETAIL_SEGMENTS]}
    for r in flags:
        if r["segment_key"] not in top_keys:
            continue
        seg = grouped.get(r["segment_key"], {})
        media = top_driver(seg.get("media", []))
        campaign = top_driver(seg.get("campaign", []))
        creative = top_driver(seg.get("creative", []))
        bundle = top_driver(seg.get("bundle", []))
        bullets = []
        if media:
            bullets.append(
                f"媒体侧：{esc(media['dim_name'])} 本期占比 {fnum(media['curr_share']):.1f}%，CPI {cpi(media['curr_cpi'])}，CPM变化 {pct(media['cpm_chg_pct'])}。"
            )
        if campaign:
            bullets.append(
                f"Campaign：{esc(campaign['dim_name'])} 本期消耗 {money(campaign['curr_spend'])}，事件 {esc(campaign.get('dim_sub') or 'n/a')}，CPI {cpi(campaign['curr_cpi'])}。"
            )
        if creative:
            bullets.append(
                f"创意侧：{esc(creative['dim_name'])} / {esc(creative.get('dim_sub') or '')} 本期消耗 {money(creative['curr_spend'])}，CPI {cpi(creative['curr_cpi'])}。"
            )
        if bundle:
            bullets.append(
                f"Bundle：{esc(bundle['dim_name'])} 本期占比 {fnum(bundle['curr_share']):.1f}%，CPI {cpi(bundle['curr_cpi'])}。"
            )
        blocks.append(
            f"""
            <section class="seg-block" id="seg-{esc(r['segment_key']).replace('|','-')}">
              <div class="seg-head">
                <div>
                  <h3>{esc(r['region'])} · {esc(r['os'])} · App {esc(r['app_id'])}</h3>
                  <p>Sandbox benchmark: CPI {cpi(r['prev_cpi'])} → {cpi(r['curr_cpi'])} ({pct(r['cpi_chg_pct'])}); DNU {num(r['prev_dnu'])} → {num(r['curr_dnu'])} ({pct(r['dnu_chg_pct'])})</p>
                </div>
                <span class="pill {cls_change(r['cpi_chg_pct'])}">{esc(r['trigger_metric'])}</span>
              </div>
              <div class="why">{''.join(f'<p>{b}</p>' for b in bullets) or '<p>Moloco 明细未匹配到足够数据。</p>'}</div>
              {render_detail_table(seg.get('campaign', []), '投放 Campaign / 事件')}
              {render_detail_table(seg.get('media', []), '媒体渠道 / Exchange')}
              {render_detail_table(seg.get('creative', []), '创意组 / 版位')}
              {render_detail_table(seg.get('bundle', []), 'Bundle ID / 子渠道')}
            </section>
            """
        )
    return "\n".join(blocks)


def render_html(flags: list[dict[str, str]], details) -> str:
    grouped = group_details(details)
    total = len(flags)
    cpi_up = sum(1 for r in flags if fnum(r["cpi_chg_pct"]) >= 10)
    cpi_down = sum(1 for r in flags if fnum(r["cpi_chg_pct"]) <= -10)
    dnu_moves = sum(1 for r in flags if abs(fnum(r["dnu_chg_pct"])) >= 10)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TT 双周波动归因看板</title>
<style>
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#f6f7fb; color:#172033; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif; font-size:13px; }}
#pw-gate {{ position:fixed; inset:0; z-index:99; background:#111827; display:flex; align-items:center; justify-content:center; }}
#pw-box {{ width:320px; background:white; border-radius:14px; padding:28px; box-shadow:0 20px 60px rgba(0,0,0,.35); text-align:center; }}
#pw-input {{ width:100%; margin-top:14px; padding:10px 12px; border:1px solid #d6dce8; border-radius:8px; text-align:center; letter-spacing:3px; }}
#pw-btn {{ width:100%; margin-top:12px; padding:10px; border:0; border-radius:8px; background:#3b5bdb; color:white; font-weight:700; cursor:pointer; }}
.page {{ max-width:1320px; margin:0 auto; padding:20px; }}
.hero {{ background:#14213d; color:white; border-radius:12px; padding:22px 26px; }}
.hero h1 {{ margin:0; font-size:22px; }}
.hero p {{ margin:8px 0 0; color:#cbd5e1; }}
.nav {{ display:flex; gap:8px; margin:14px 0; }}
.nav button {{ border:1px solid #d6dce8; background:white; padding:9px 14px; border-radius:8px; cursor:pointer; font-weight:700; color:#475569; }}
.nav button.active {{ background:#253858; color:white; border-color:#253858; }}
.tab {{ display:none; }}
.tab.active {{ display:block; }}
.cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:14px 0; }}
.card {{ background:white; border:1px solid #e3e8f2; border-radius:10px; padding:14px 16px; }}
.card .label {{ color:#64748b; font-size:12px; }}
.card .value {{ font-size:24px; font-weight:800; margin-top:4px; }}
.note {{ background:#fff7ed; border-left:4px solid #f97316; padding:12px 14px; border-radius:8px; color:#7c2d12; margin:12px 0; }}
table {{ width:100%; border-collapse:collapse; background:white; border:1px solid #e3e8f2; border-radius:10px; overflow:hidden; }}
th {{ background:#f8fafc; color:#64748b; font-size:11px; text-align:left; padding:8px 10px; border-bottom:1px solid #e3e8f2; white-space:nowrap; }}
td {{ padding:8px 10px; border-bottom:1px solid #eef2f7; white-space:nowrap; }}
tr:hover td {{ background:#fbfdff; }}
.up {{ color:#dc2626; font-weight:700; }}
.down {{ color:#059669; font-weight:700; }}
.flat {{ color:#64748b; }}
a {{ color:#2563eb; text-decoration:none; font-weight:700; }}
.seg-block {{ background:white; border:1px solid #e3e8f2; border-radius:12px; margin:0 0 16px; overflow:hidden; }}
.seg-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:16px 18px; border-bottom:1px solid #eef2f7; background:#fbfdff; }}
.seg-head h3 {{ margin:0; font-size:16px; }}
.seg-head p {{ margin:6px 0 0; color:#64748b; }}
.pill {{ display:inline-flex; padding:4px 10px; border-radius:999px; background:#eef2ff; }}
.why {{ padding:12px 18px; background:#f8fafc; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px 18px; }}
.why p {{ margin:0; color:#334155; line-height:1.45; }}
.detail-table {{ padding:12px 18px 16px; }}
.detail-table h4 {{ margin:0 0 8px; color:#334155; font-size:13px; }}
.name {{ max-width:360px; overflow:hidden; text-overflow:ellipsis; }}
.name span {{ display:block; color:#94a3b8; font-size:11px; margin-top:2px; overflow:hidden; text-overflow:ellipsis; }}
.empty {{ padding:10px 12px; background:#f8fafc; border:1px dashed #d6dce8; color:#94a3b8; border-radius:8px; }}
.source {{ margin-top:16px; color:#64748b; font-size:12px; line-height:1.6; }}
@media(max-width:900px) {{ .cards {{ grid-template-columns:1fr 1fr; }} .why {{ grid-template-columns:1fr; }} .page {{ padding:12px; }} table {{ font-size:11px; }} }}
</style>
</head>
<body>
<div id="pw-gate"><div id="pw-box"><h2>TT 双周报</h2><div>请输入访问密码</div><input id="pw-input" type="password" onkeydown="if(event.key==='Enter')checkPw()"><button id="pw-btn" onclick="checkPw()">进入</button><div id="pw-err" style="color:#dc2626;margin-top:8px;font-size:12px;"></div></div></div>
<div class="page">
  <section class="hero">
    <h1>TT 双周波动归因看板</h1>
    <p>Benchmark: sandbox.sherry · 明细支撑: Moloco BQ Agent / athena fact 表 · 本期 {CURR_START} ~ {CURR_END} · 对比 {PREV_START} ~ {PREV_END} · 生成 {generated}</p>
  </section>
  <div class="nav"><button id="btn-overview" onclick="showTab('overview')">双周纵览</button><button id="btn-detail" onclick="showTab('detail')">归因详情</button><a style="margin-left:auto;align-self:center;" href="./index.html">返回周报</a></div>

  <section id="overview" class="tab">
    <div class="cards">
      <div class="card"><div class="label">触发波动 Segment</div><div class="value">{total}</div></div>
      <div class="card"><div class="label">CPI 上升 ≥10%</div><div class="value up">{cpi_up}</div></div>
      <div class="card"><div class="label">CPI 下降 ≥10%</div><div class="value down">{cpi_down}</div></div>
      <div class="card"><div class="label">DNU 波动 ≥10%</div><div class="value">{dnu_moves}</div></div>
    </div>
    <div class="note">决策口径：先用 sandbox 的国家 × OS × app_id 双周 DNU / Blackswan CPI 波动做 benchmark 触发，再用 Moloco 明细解释媒体、campaign/事件、创意、bundle 结构变化。试跑版详情展开当前双周消耗 Top {MAX_DETAIL_SEGMENTS} 的波动项。</div>
    <table>
      <thead><tr><th>国家</th><th>OS</th><th>App ID</th><th>触发</th><th>本期消耗</th><th>本期 DNU</th><th>Blackswan CPI</th><th>CPI变化</th><th>DNU变化</th><th>详情</th></tr></thead>
      <tbody>{render_overview_rows(flags)}</tbody>
    </table>
  </section>

  <section id="detail" class="tab">
    {render_detail_blocks(flags, grouped)}
  </section>

  <div class="source">
    <strong>Source</strong><br>
    Benchmark: <code>ads-bpd-guard-sandbox.sherry.tt_android_region_daily</code>, <code>tt_ios_region_daily</code>, campaign bridge from <code>tt_android_campaign_daily</code>/<code>tt_ios_campaign_daily</code>.<br>
    Moloco details: <code>ads-bpd-guard-china.athena.fact_dsp_core</code>, <code>fact_dsp_creative</code>, <code>fact_dsp_publisher</code>. CPI = spend / installs or spend / DNU; CPM = spend / impressions × 1000; IPM = installs / impressions × 1000.
  </div>
</div>
<script>
function checkPw() {{
  const v = document.getElementById('pw-input').value;
  if (v === 'TT') {{
    sessionStorage.setItem('tt_auth','1');
    document.getElementById('pw-gate').style.display='none';
  }} else {{
    document.getElementById('pw-err').textContent='密码错误';
    document.getElementById('pw-input').value='';
  }}
}}
if (sessionStorage.getItem('tt_auth') === '1') document.getElementById('pw-gate').style.display='none';
function showTab(id) {{
  for (const k of ['overview','detail']) {{
    document.getElementById(k).classList.remove('active');
    document.getElementById('btn-'+k).classList.remove('active');
  }}
  document.getElementById(id).classList.add('active');
  document.getElementById('btn-'+id).classList.add('active');
}}
showTab('overview');
</script>
</body>
</html>"""


def main():
    flags, details = load_data()
    html_text = render_html(flags, details)
    OUTPUT_FILE.write_text(html_text, encoding="utf-8")
    print(f"generated {OUTPUT_FILE}")
    print(f"flags={len(flags)} detail_rows={sum(len(v) for v in details.values())}")


if __name__ == "__main__":
    main()
