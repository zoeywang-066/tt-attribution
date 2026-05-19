#!/usr/bin/env python3
"""
TikTok 投放数据 CPI 归因报告生成器
每周一运行，覆盖上上周周日到上周周六 vs 前一个7天
运行方式：python3 generate_tt_report.py
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime

REPO_DIR = Path(__file__).parent
OUTPUT_FILE = str(REPO_DIR / "index.html")

# ─── 报告数据（每周由 Claude 更新此部分）─────────────────────────────────────
REPORT_DATA = {
    "period_curr": "2026-05-10 ~ 2026-05-16",
    "period_prev": "2026-05-03 ~ 2026-05-09",
    "generated_at": "2026-05-19",

    # ── 产品 1340 ──────────────────────────────────────────────────────────
    "p1340": {
        "product_id": "dP2o4r09cpwZxpzy",
        "label": "TikTok Lite",
        "countries": [
            {
                "code": "BRA", "flag": "🇧🇷", "name": "BRA（巴西）",
                "prev_cpi": 0.45, "curr_cpi": 0.59, "cpi_chg": 32.6,
                "prev_cpm": 1.84, "curr_cpm": 2.24, "cpm_chg": 21.7,
                "prev_ipm": 4.11, "curr_ipm": 3.78, "ipm_chg": -8.2,
                "prev_ctr": 37.71, "curr_ctr": 37.25,
                "prev_cvr": 1.09, "curr_cvr": 1.01,
                "prev_spend": 2584.89, "curr_spend": 2898.68,
                "prev_installs": 5773, "curr_installs": 4882,
                "media_pct": 70, "creative_pct": 30,
                "conclusion": "CPM 全面上涨是主因（贡献70%），叠加 IPM 轻微下滑。MOLOCO_SDK_MAX 的 CPM 暴涨 +55.5% 且花费占比扩大至12.4%，是最大成本拖累。install campaign 的 CVR 从1.09%降至0.94%，需检查素材是否疲劳。建议：审视 SDK_MAX 出价策略，排查 ADX_RTB/INMOBI 流量质量下滑原因。",
                "campaigns": [
                    {"name": "TikTokLite CPA_tt_d2_retention_user", "prev_spend": 1402.52, "curr_spend": 1550.02,
                     "prev_cpi": 0.45, "curr_cpi": 0.57, "cpi_chg": 28.2,
                     "prev_cpm": 1.99, "curr_cpm": 2.40, "cpm_chg": 20.7,
                     "prev_ipm": 4.44, "curr_ipm": 4.18, "ipm_chg": -5.9,
                     "prev_ctr": 40.58, "curr_ctr": 38.53, "prev_cvr": 1.09, "curr_cvr": 1.08,
                     "type": "creative"},
                    {"name": "TikTokLite_install", "prev_spend": 1182.37, "curr_spend": 1348.66,
                     "prev_cpi": 0.45, "curr_cpi": 0.62, "cpi_chg": 38.0,
                     "prev_cpm": 1.70, "curr_cpm": 2.09, "cpm_chg": 23.0,
                     "prev_ipm": 3.79, "curr_ipm": 3.37, "ipm_chg": -10.9,
                     "prev_ctr": 34.81, "curr_ctr": 35.96, "prev_cvr": 1.09, "curr_cvr": 0.94,
                     "type": "both"},
                ],
                "exchanges": [
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 10.0, "curr_share": 12.4, "share_chg": 2.4,
                     "prev_cpi": 0.46, "curr_cpi": 0.79, "cpi_chg": 73.1,
                     "prev_cpm_chg": 55.5, "ipm_chg": -10.2, "type": "media"},
                    {"name": "INMOBI", "prev_share": 19.0, "curr_share": 20.0, "share_chg": 1.0,
                     "prev_cpi": 0.48, "curr_cpi": 0.72, "cpi_chg": 49.1,
                     "prev_cpm_chg": 21.1, "ipm_chg": -18.8, "type": "both"},
                    {"name": "ADX_RTB", "prev_share": 6.7, "curr_share": 8.0, "share_chg": 1.3,
                     "prev_cpi": 0.33, "curr_cpi": 0.51, "cpi_chg": 51.9,
                     "prev_cpm_chg": 14.8, "ipm_chg": -24.5, "type": "creative"},
                    {"name": "XIAOMI", "prev_share": 20.0, "curr_share": 18.0, "share_chg": -2.0,
                     "prev_cpi": 0.41, "curr_cpi": 0.52, "cpi_chg": 25.1,
                     "prev_cpm_chg": 5.7, "ipm_chg": -15.5, "type": "creative"},
                    {"name": "FYBER", "prev_share": 15.6, "curr_share": 13.7, "share_chg": -1.9,
                     "prev_cpi": 0.45, "curr_cpi": 0.56, "cpi_chg": 23.0,
                     "prev_cpm_chg": 19.6, "ipm_chg": -2.8, "type": "media"},
                    {"name": "VUNGLE", "prev_share": 10.1, "curr_share": 9.6, "share_chg": -0.5,
                     "prev_cpi": 0.55, "curr_cpi": 0.60, "cpi_chg": 9.7,
                     "prev_cpm_chg": 25.0, "ipm_chg": 14.0, "type": "ok"},
                ],
            }
        ],
    },

    # ── 产品 1180 ──────────────────────────────────────────────────────────
    "p1180": {
        "product_id": "OK9ZHF0eYCoGIUfq",
        "label": "1180",
        "no_alert": True,
        "all_countries": [
            {"code": "IDN", "flag": "🇮🇩", "name": "IDN", "prev_cpi": 2.10, "curr_cpi": 2.21, "cpi_chg": 5.21,
             "prev_cpm": 4.26, "curr_cpm": 4.14, "prev_ipm": 2.03, "curr_ipm": 1.87},
            {"code": "PHL", "flag": "🇵🇭", "name": "PHL", "prev_cpi": 2.70, "curr_cpi": 2.73, "cpi_chg": 1.16,
             "prev_cpm": 7.37, "curr_cpm": 7.23, "prev_ipm": 2.73, "curr_ipm": 2.65},
            {"code": "JPN", "flag": "🇯🇵", "name": "JPN", "prev_cpi": 7.96, "curr_cpi": 7.43, "cpi_chg": -6.63,
             "prev_cpm": 1.26, "curr_cpm": 1.27, "prev_ipm": 0.16, "curr_ipm": 0.17},
            {"code": "KOR", "flag": "🇰🇷", "name": "KOR", "prev_cpi": 7.63, "curr_cpi": 7.09, "cpi_chg": -7.04,
             "prev_cpm": 1.94, "curr_cpm": 2.02, "prev_ipm": 0.25, "curr_ipm": 0.29},
            {"code": "THA", "flag": "🇹🇭", "name": "THA", "prev_cpi": 5.00, "curr_cpi": 4.62, "cpi_chg": -7.56,
             "prev_cpm": 10.94, "curr_cpm": 10.65, "prev_ipm": 2.19, "curr_ipm": 2.31},
            {"code": "MYS", "flag": "🇲🇾", "name": "MYS", "prev_cpi": 3.17, "curr_cpi": 2.83, "cpi_chg": -10.77,
             "prev_cpm": 7.86, "curr_cpm": 7.75, "prev_ipm": 2.48, "curr_ipm": 2.74},
            {"code": "VNM", "flag": "🇻🇳", "name": "VNM", "prev_cpi": 5.72, "curr_cpi": 4.90, "cpi_chg": -14.20,
             "prev_cpm": 10.12, "curr_cpm": 9.68, "prev_ipm": 1.77, "curr_ipm": 1.97},
            {"code": "KHM", "flag": "🇰🇭", "name": "KHM", "prev_cpi": 1.09, "curr_cpi": 0.89, "cpi_chg": -17.92,
             "prev_cpm": 3.22, "curr_cpm": 3.08, "prev_ipm": 2.96, "curr_ipm": 3.45},
        ],
    },

    # ── 产品 1233 ──────────────────────────────────────────────────────────
    "p1233": {
        "product_id": "IP3KqTHC6BNDf4CT",
        "label": "1233",
        "countries": [
            {
                "code": "PRY", "flag": "🇵🇾", "name": "PRY（巴拉圭）",
                "prev_cpi": 0.74, "curr_cpi": 0.97, "cpi_chg": 31.2,
                "prev_cpm": 2.29, "curr_cpm": 2.40, "cpm_chg": 4.8,
                "prev_ipm": 3.09, "curr_ipm": 2.47, "ipm_chg": -20.1,
                "prev_ctr": 36.00, "curr_ctr": 35.40,
                "prev_cvr": 0.86, "curr_cvr": 0.70,
                "prev_spend": 101.75, "curr_spend": 102.32,
                "prev_installs": 137, "curr_installs": 105,
                "media_pct": 17, "creative_pct": 83,
                "conclusion": "CVR 下降 -18.6% 是核心，用户点击后安装率大幅降低，属于创意/落地页效率下降信号。DNU 和 bs_conversion_0330 两个 campaign CPI 近乎翻倍，bs_conversion_0429 表现正常。INMOBI 和 SDK_ADMOB 的 IPM 大幅崩塌，与 campaign 恶化趋势一致。建议：优先排查 DNU 和 0330 campaign 素材是否疲劳。",
                "campaigns": [
                    {"name": "DNU", "prev_spend": 38, "curr_spend": 43,
                     "prev_cpi": 0.84, "curr_cpi": 1.42, "cpi_chg": 68.1,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -35.2,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "bs_conversion_0330", "prev_spend": 34, "curr_spend": 33,
                     "prev_cpi": 0.64, "curr_cpi": 1.01, "cpi_chg": 56.4,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -35.3,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "bs_conversion_0429", "prev_spend": 30, "curr_spend": 27,
                     "prev_cpi": 0.75, "curr_cpi": 0.68, "cpi_chg": -9.1,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 11.1,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                ],
                "exchanges": [
                    {"name": "VUNGLE", "prev_share": 32.5, "curr_share": 30.4, "share_chg": -2.1,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 24.0,
                     "prev_cpm_chg": 12.5, "ipm_chg": -9.3, "type": "both"},
                    {"name": "INMOBI", "prev_share": 23.5, "curr_share": 23.5, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 48.1,
                     "prev_cpm_chg": 13.0, "ipm_chg": -23.7, "type": "creative"},
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 19.0, "curr_share": 19.0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 2.2,
                     "prev_cpm_chg": 0, "ipm_chg": 0, "type": "ok"},
                    {"name": "SDK_ADMOB", "prev_share": 0, "curr_share": 0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 56.3,
                     "prev_cpm_chg": 0, "ipm_chg": -33.4, "type": "creative"},
                ],
            },
            {
                "code": "MOZ", "flag": "🇲🇿", "name": "MOZ（莫桑比克）",
                "prev_cpi": 0.46, "curr_cpi": 0.55, "cpi_chg": 20.1,
                "prev_cpm": 1.41, "curr_cpm": 1.42, "cpm_chg": 0.6,
                "prev_ipm": 3.09, "curr_ipm": 2.59, "ipm_chg": -16.2,
                "prev_ctr": 27.09, "curr_ctr": 22.82,
                "prev_cvr": 1.14, "curr_cvr": 1.14,
                "prev_spend": 57.44, "curr_spend": 64.03,
                "prev_installs": 126, "curr_installs": 117,
                "media_pct": 3, "creative_pct": 97,
                "conclusion": "CTR 大幅下滑（27.1%→22.8%），用户点击意愿降低，是典型的创意疲劳信号。VUNGLE 份额扩大 +7.5pp 但 IPM 同时暴跌 -31.7%，双重恶化。IRONSOURCE 和 SDK_MAX 表现优秀（IPM 大幅提升），但预算流向了低效渠道。建议：更换素材，将预算从 VUNGLE 转至 IRONSOURCE/SDK_MAX。",
                "campaigns": [
                    {"name": "bs_conversion", "prev_spend": 32, "curr_spend": 36,
                     "prev_cpi": 0.45, "curr_cpi": 0.60, "cpi_chg": 34.8,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -26.6,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "DNU", "prev_spend": 25, "curr_spend": 28,
                     "prev_cpi": 0.47, "curr_cpi": 0.49, "cpi_chg": 4.4,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 0,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                ],
                "exchanges": [
                    {"name": "VUNGLE", "prev_share": 39.2, "curr_share": 46.7, "share_chg": 7.5,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 42.9,
                     "prev_cpm_chg": 0, "ipm_chg": -31.7, "type": "creative"},
                    {"name": "INMOBI", "prev_share": 33.0, "curr_share": 33.0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 31.4,
                     "prev_cpm_chg": 0, "ipm_chg": -23.7, "type": "creative"},
                    {"name": "IRONSOURCE", "prev_share": 0, "curr_share": 0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -37.2,
                     "prev_cpm_chg": 0, "ipm_chg": 54.2, "type": "ok"},
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 0, "curr_share": 0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -84.3,
                     "prev_cpm_chg": 0, "ipm_chg": 478.0, "type": "ok"},
                ],
            },
            {
                "code": "DEU", "flag": "🇩🇪", "name": "DEU（德国）",
                "prev_cpi": 18.82, "curr_cpi": 22.43, "cpi_chg": 19.2,
                "prev_cpm": 15.35, "curr_cpm": 14.43, "cpm_chg": -6.0,
                "prev_ipm": 0.82, "curr_ipm": 0.64, "ipm_chg": -21.2,
                "prev_ctr": 30.93, "curr_ctr": 28.53,
                "prev_cvr": 0.26, "curr_cvr": 0.23,
                "prev_spend": 3971.86, "curr_spend": 4082.45,
                "prev_installs": 211, "curr_installs": 182,
                "media_pct": 0, "creative_pct": 100,
                "conclusion": "CPM 下降（买量变便宜）但 CPI 仍涨 19%，完全由 IPM 下滑驱动。主力 campaign af_bs_conversion IPM 跌 -35%，而 Playable 素材 campaign 表现良好甚至改善，印证是素材/创意问题而非媒体竞价问题。IRONSOURCE 和 UNITY 的 IPM 几乎归零，建议暂停或大幅降低这两个渠道出价。",
                "campaigns": [
                    {"name": "af_bs_conversion", "prev_spend": 1628, "curr_spend": 1673,
                     "prev_cpi": 15.62, "curr_cpi": 21.71, "cpi_chg": 38.9,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -35.1,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "webcast_gift", "prev_spend": 278, "curr_spend": 286,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 18.3,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -15.0,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "pltv_lt7_copear", "prev_spend": 675, "curr_spend": 694,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 9.0,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 0,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                    {"name": "af_bs_conversion_playable", "prev_spend": 397, "curr_spend": 408,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -3.2,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 5.0,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                ],
                "exchanges": [
                    {"name": "IRONSOURCE", "prev_share": 0, "curr_share": 0, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 361.8,
                     "prev_cpm_chg": 0, "ipm_chg": -80.0, "type": "creative"},
                    {"name": "UNITY", "prev_share": 0, "curr_share": 6.7, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 112.1,
                     "prev_cpm_chg": 0, "ipm_chg": -53.8, "type": "creative"},
                    {"name": "ADX_RTB", "prev_share": 0, "curr_share": 15.3, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 33.3,
                     "prev_cpm_chg": 0, "ipm_chg": -23.7, "type": "creative"},
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 0, "curr_share": 19.8, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 21.3,
                     "prev_cpm_chg": 0, "ipm_chg": -26.4, "type": "creative"},
                    {"name": "VUNGLE", "prev_share": 0, "curr_share": 13.9, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -3.0,
                     "prev_cpm_chg": 0, "ipm_chg": 0, "type": "ok"},
                ],
            },
            {
                "code": "IRQ", "flag": "🇮🇶", "name": "IRQ（伊拉克）",
                "prev_cpi": 1.46, "curr_cpi": 1.73, "cpi_chg": 19.2,
                "prev_cpm": 3.62, "curr_cpm": 3.80, "cpm_chg": 4.8,
                "prev_ipm": 2.49, "curr_ipm": 2.19, "ipm_chg": -12.1,
                "prev_ctr": 49.67, "curr_ctr": 49.09,
                "prev_cvr": 0.50, "curr_cvr": 0.45,
                "prev_spend": 227.06, "curr_spend": 241.08,
                "prev_installs": 156, "curr_installs": 139,
                "media_pct": 27, "creative_pct": 73,
                "conclusion": "三个 campaign 全部恶化，CVR 均有下滑，是系统性创意转化问题。FYBER 效率最好（IPM +13%）但份额反而缩减了 -2pp。XIAOMI 的 IPM 暴跌 -37%。建议：增加 FYBER 预算配比，排查 XIAOMI 渠道流量质量，检查三个 campaign 是否素材需要更新。",
                "campaigns": [
                    {"name": "bs_conversion_0330", "prev_spend": 0, "curr_spend": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 25.8,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -15.5,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "bs_conversion_0511", "prev_spend": 0, "curr_spend": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 12.4,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -6.6,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                    {"name": "DNU", "prev_spend": 0, "curr_spend": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 17.9,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -13.4,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                ],
                "exchanges": [
                    {"name": "INMOBI", "prev_share": 37.1, "curr_share": 38.7, "share_chg": 1.6,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 25.4,
                     "prev_cpm_chg": 5.7, "ipm_chg": -15.7, "type": "both"},
                    {"name": "VUNGLE", "prev_share": 22.7, "curr_share": 22.7, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 18.8,
                     "prev_cpm_chg": 7.8, "ipm_chg": -9.2, "type": "both"},
                    {"name": "XIAOMI", "prev_share": 5.6, "curr_share": 5.6, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 81.5,
                     "prev_cpm_chg": 0, "ipm_chg": -37.2, "type": "creative"},
                    {"name": "FYBER", "prev_share": 17.5, "curr_share": 15.5, "share_chg": -2.0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -13.4,
                     "prev_cpm_chg": 0, "ipm_chg": 13.0, "type": "ok"},
                    {"name": "IRONSOURCE", "prev_share": 16.7, "curr_share": 16.7, "share_chg": 0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 1.5,
                     "prev_cpm_chg": 0, "ipm_chg": 0, "type": "ok"},
                ],
            },
            {
                "code": "NLD", "flag": "🇳🇱", "name": "NLD（荷兰）",
                "prev_cpi": 3.17, "curr_cpi": 3.76, "cpi_chg": 18.9,
                "prev_cpm": 3.85, "curr_cpm": 3.69, "cpm_chg": -4.0,
                "prev_ipm": 1.22, "curr_ipm": 0.98, "ipm_chg": -19.3,
                "prev_ctr": 22.23, "curr_ctr": 19.99,
                "prev_cvr": 0.55, "curr_cvr": 0.49,
                "prev_spend": 224.76, "curr_spend": 237.13,
                "prev_installs": 71, "curr_installs": 63,
                "media_pct": 0, "creative_pct": 100,
                "conclusion": "CPM 下降（利好）但 CPI 仍涨 19%，证明是纯粹创意转化问题。MOLOCO_SDK_MAX 效率大幅提升（IPM +25%）但份额反而降了 3.7pp，INMOBI（CPI +90%，IPM -46%）和 ADX_RTB（CPI +44%）低效扩张。建议：大幅增加 SDK_MAX 预算，压缩 INMOBI 投放，并检查 CTR 下降是否为素材问题。",
                "campaigns": [
                    {"name": "bs_conversion_0513", "prev_spend": 225, "curr_spend": 237,
                     "prev_cpi": 3.17, "curr_cpi": 3.76, "cpi_chg": 18.9,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": -4.0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -19.3,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "creative"},
                ],
                "exchanges": [
                    {"name": "INMOBI", "prev_share": 0, "curr_share": 11.5, "share_chg": 1.5,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 90.3,
                     "prev_cpm_chg": 0, "ipm_chg": -45.9, "type": "creative"},
                    {"name": "ADX_RTB", "prev_share": 0, "curr_share": 16.5, "share_chg": 1.0,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 43.8,
                     "prev_cpm_chg": 8.7, "ipm_chg": -24.4, "type": "both"},
                    {"name": "VUNGLE", "prev_share": 24.3, "curr_share": 25.9, "share_chg": 1.6,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 19.3,
                     "prev_cpm_chg": 2.8, "ipm_chg": -21.3, "type": "creative"},
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 25.6, "curr_share": 21.9, "share_chg": -3.7,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -29.8,
                     "prev_cpm_chg": 0, "ipm_chg": 25.0, "type": "ok"},
                ],
            },
            {
                "code": "SAU", "flag": "🇸🇦", "name": "SAU（沙特）",
                "prev_cpi": 2.10, "curr_cpi": 2.48, "cpi_chg": 18.1,
                "prev_cpm": 5.05, "curr_cpm": 5.68, "cpm_chg": 12.4,
                "prev_ipm": 2.41, "curr_ipm": 2.29, "ipm_chg": -4.9,
                "prev_ctr": 38.52, "curr_ctr": 39.11,
                "prev_cvr": 0.62, "curr_cvr": 0.59,
                "prev_spend": 1019.11, "curr_spend": 1104.48,
                "prev_installs": 485, "curr_installs": 445,
                "media_pct": 70, "creative_pct": 30,
                "conclusion": "SAU 是本周唯一以媒体成本上涨为主因的国家（CPM 贡献70%）。pltv_lt7_deeplt campaign 的 CPM 暴涨 +25.3%，可能与出价策略或市场竞价加剧有关。af_bs_conversion_rt 表现正常（CPI +4.4%）。建议：重点检查 pltv campaign 的 TKPI 目标出价设置。",
                "campaigns": [
                    {"name": "pltv_lt7_deeplt", "prev_spend": 510, "curr_spend": 552,
                     "prev_cpi": 2.14, "curr_cpi": 2.94, "cpi_chg": 37.0,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 25.3,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -8.6,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "media"},
                    {"name": "af_bs_conversion_rt", "prev_spend": 509, "curr_spend": 552,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 4.4,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 7.2,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 2.6,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                ],
                "exchanges": [],
            },
            {
                "code": "BGD", "flag": "🇧🇩", "name": "BGD（孟加拉）",
                "prev_cpi": 0.45, "curr_cpi": 0.49, "cpi_chg": 10.1,
                "prev_cpm": 1.39, "curr_cpm": 1.46, "cpm_chg": 5.1,
                "prev_ipm": 3.10, "curr_ipm": 2.96, "ipm_chg": -4.6,
                "prev_ctr": 42.25, "curr_ctr": 38.75,
                "prev_cvr": 0.73, "curr_cvr": 0.76,
                "prev_spend": 716.31, "curr_spend": 747.55,
                "prev_installs": 1595, "curr_installs": 1512,
                "media_pct": 51, "creative_pct": 49,
                "conclusion": "媒体侧（VUNGLE CPM +23%）和创意侧（CTR -8.3%）各贡献约一半。高效渠道（SDK_MAX、UNITY）份额缩减，低效渠道（INMOBI+VUNGLE）份额合计扩大 +7.2pp，形成结构性成本压力。建议：将部分预算从 VUNGLE 转向 SDK_MAX 和 UNITY。",
                "campaigns": [
                    {"name": "bs_conversion", "prev_spend": 516, "curr_spend": 541,
                     "prev_cpi": 0.41, "curr_cpi": 0.46, "cpi_chg": 12.2,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 10.5,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": -1.6,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "media"},
                    {"name": "install", "prev_spend": 200, "curr_spend": 207,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 3.2,
                     "prev_cpm": None, "curr_cpm": None, "cpm_chg": 0,
                     "prev_ipm": None, "curr_ipm": None, "ipm_chg": 0,
                     "prev_ctr": None, "curr_ctr": None, "prev_cvr": None, "curr_cvr": None,
                     "type": "ok"},
                ],
                "exchanges": [
                    {"name": "INMOBI", "prev_share": 32.0, "curr_share": 36.4, "share_chg": 4.4,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 16.3,
                     "prev_cpm_chg": 5.3, "ipm_chg": -9.5, "type": "both"},
                    {"name": "VUNGLE", "prev_share": 26.2, "curr_share": 29.0, "share_chg": 2.8,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": 31.9,
                     "prev_cpm_chg": 23.4, "ipm_chg": -6.4, "type": "media"},
                    {"name": "MOLOCO_SDK_MAX", "prev_share": 11.7, "curr_share": 9.0, "share_chg": -2.7,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -2.0,
                     "prev_cpm_chg": 0, "ipm_chg": 0, "type": "ok"},
                    {"name": "UNITY", "prev_share": 6.2, "curr_share": 5.4, "share_chg": -0.8,
                     "prev_cpi": None, "curr_cpi": None, "cpi_chg": -12.9,
                     "prev_cpm_chg": 0, "ipm_chg": 11.0, "type": "ok"},
                ],
            },
        ],
    },
}

# ─── HTML 生成 ───────────────────────────────────────────────────────────────
def chg_class(v):
    if v > 0: return "chg-up"
    if v < 0: return "chg-down"
    return "chg-flat"

def chg_str(v, prefix="", suffix="%", decimals=1):
    if v is None: return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.{decimals}f}{suffix}"

def attr_badge(media_pct, creative_pct):
    if media_pct >= 60:
        return '<span class="attr-badge attr-media">媒体侧主导</span>'
    elif creative_pct >= 60:
        return '<span class="attr-badge attr-creative">创意侧主导</span>'
    else:
        return '<span class="attr-badge attr-both">媒体+创意共同</span>'

def type_tag(t):
    tags = {
        "media": '<span class="tag tag-warn">媒体侧CPM↑</span>',
        "creative": '<span class="tag tag-warn">创意侧IPM↓</span>',
        "both": '<span class="tag tag-warn">CPM↑+IPM↓</span>',
        "ok": '<span class="tag tag-ok">正常/改善</span>',
    }
    return tags.get(t, "")

def render_country_block(c):
    media = c["media_pct"]
    creative = c["creative_pct"]
    # clamp
    mbar = max(0, min(100, media if media > 0 else 0))
    cbar = max(0, min(100, creative if creative > 0 else 0))
    if mbar + cbar > 100:
        total = mbar + cbar
        mbar = int(mbar / total * 100)
        cbar = 100 - mbar

    campaigns_html = ""
    if c.get("campaigns"):
        rows = ""
        for cam in c["campaigns"]:
            cpi_prev = f"${cam['prev_cpi']:.2f}" if cam.get("prev_cpi") else "—"
            cpi_curr = f"${cam['curr_cpi']:.2f}" if cam.get("curr_cpi") else "—"
            rows += f"""
            <tr>
              <td class="name-cell" title="{cam['name']}">{cam['name'][:40]}{'…' if len(cam['name'])>40 else ''}</td>
              <td>{cpi_prev}</td><td>{cpi_curr}</td>
              <td class="{chg_class(cam['cpi_chg'])}">{chg_str(cam['cpi_chg'])}</td>
              <td class="{chg_class(cam['cpm_chg'])}">{chg_str(cam['cpm_chg'])}</td>
              <td class="{chg_class(cam['ipm_chg'])}">{chg_str(cam['ipm_chg'])}</td>
              <td>{type_tag(cam['type'])}</td>
            </tr>"""
        campaigns_html = f"""
        <div class="table-title"><span class="icon icon-creative">C</span>Campaign 明细</div>
        <table>
          <tr><th>Campaign</th><th>CPI 上期</th><th>CPI 本期</th><th>CPI 变化</th><th>CPM 变化</th><th>IPM 变化</th><th>类型</th></tr>
          {rows}
        </table>"""

    exchanges_html = ""
    if c.get("exchanges"):
        rows = ""
        for ex in c["exchanges"]:
            share_str = f"{chg_str(ex['share_chg'], suffix='pp')} {'⚠' if ex['share_chg'] >= 2 else ('↓' if ex['share_chg'] <= -2 else '')}" if ex['share_chg'] != 0 else "—"
            share_cls = "share-up" if ex['share_chg'] > 1 else ("share-down" if ex['share_chg'] < -1 else "chg-flat")
            rows += f"""
            <tr>
              <td>{ex['name']}</td>
              <td>{ex['prev_share']:.1f}%</td><td>{ex['curr_share']:.1f}%</td>
              <td class="{share_cls}">{share_str}</td>
              <td class="{chg_class(ex['cpi_chg'])}">{chg_str(ex['cpi_chg'])}</td>
              <td class="{chg_class(ex['prev_cpm_chg'])}">{chg_str(ex['prev_cpm_chg'])}</td>
              <td class="{chg_class(ex['ipm_chg'])}">{chg_str(ex['ipm_chg'])}</td>
              <td>{type_tag(ex['type'])}</td>
            </tr>"""
        exchanges_html = f"""
        <div class="table-title"><span class="icon icon-media">M</span>Exchange 明细（媒体侧）</div>
        <table>
          <tr><th>Exchange</th><th>上期占比</th><th>本期占比</th><th>占比变化</th><th>CPI 变化</th><th>CPM 变化</th><th>IPM 变化</th><th>类型</th></tr>
          {rows}
        </table>"""

    ctr_row = ""
    if c.get("prev_ctr") is not None:
        ctr_chg = c["curr_ctr"] - c["prev_ctr"]
        cvr_chg = (c["curr_cvr"] - c["prev_cvr"]) / c["prev_cvr"] * 100 if c["prev_cvr"] else 0
        ctr_row = f"""
        <div class="metric-pill"><div class="m-label">CTR</div><div class="m-val">{c['prev_ctr']:.1f}%→{c['curr_ctr']:.1f}%</div><div class="m-chg {chg_class(ctr_chg)}">{chg_str(ctr_chg, suffix='pp')}</div></div>
        <div class="metric-pill"><div class="m-label">CVR</div><div class="m-val">{c['prev_cvr']:.2f}%→{c['curr_cvr']:.2f}%</div><div class="m-chg {chg_class(cvr_chg)}">{chg_str(cvr_chg)}</div></div>"""

    return f"""
  <div class="country-block">
    <div class="country-header">
      <div class="country-name">{c['flag']} {c['name']}</div>
      <span class="cpi-badge cpi-up">CPI {chg_str(c['cpi_chg'])}</span>
      {attr_badge(media, creative)}
      <div style="margin-left:auto;font-size:12px;color:#94a3b8;">${c['prev_cpi']:.2f} → ${c['curr_cpi']:.2f}</div>
    </div>
    <div class="attr-section">
      <div class="attr-bar-wrap">
        <div style="font-size:11px;color:#64748b;width:56px;">归因</div>
        <div class="attr-bar">
          <div class="attr-media-fill" style="width:{mbar}%"></div>
          <div class="attr-creative-fill" style="width:{cbar}%"></div>
        </div>
        <div class="attr-labels">
          <span><span class="dot" style="background:#f97316"></span>媒体侧 {media}%（CPM {chg_str(c['cpm_chg'])}）</span>
          <span><span class="dot" style="background:#a855f7"></span>创意侧 {creative}%（IPM {chg_str(c['ipm_chg'])}）</span>
        </div>
      </div>
    </div>
    <div class="metrics-grid">
      <div class="metric-pill"><div class="m-label">CPI</div><div class="m-val">${c['prev_cpi']:.2f}→${c['curr_cpi']:.2f}</div><div class="m-chg {chg_class(c['cpi_chg'])}">{chg_str(c['cpi_chg'])}</div></div>
      <div class="metric-pill"><div class="m-label">CPM</div><div class="m-val">${c['prev_cpm']:.2f}→${c['curr_cpm']:.2f}</div><div class="m-chg {chg_class(c['cpm_chg'])}">{chg_str(c['cpm_chg'])}</div></div>
      <div class="metric-pill"><div class="m-label">IPM</div><div class="m-val">{c['prev_ipm']:.2f}→{c['curr_ipm']:.2f}</div><div class="m-chg {chg_class(c['ipm_chg'])}">{chg_str(c['ipm_chg'])}</div></div>
      {ctr_row}
      <div class="metric-pill"><div class="m-label">花费</div><div class="m-val">${c['prev_spend']:,.0f}→${c['curr_spend']:,.0f}</div></div>
      <div class="metric-pill"><div class="m-label">安装</div><div class="m-val">{c['prev_installs']:,}→{c['curr_installs']:,}</div></div>
    </div>
    <div class="table-section">
      {campaigns_html}
      {exchanges_html}
    </div>
    <div class="conclusion"><strong>结论：</strong>{c['conclusion']}</div>
  </div>"""


def render_1180_tab(d):
    rows = ""
    for c in d["all_countries"]:
        cls = "chg-up" if c["cpi_chg"] > 0 else "chg-down"
        badge = f'<span style="font-size:11px;padding:1px 6px;border-radius:10px;background:{"#fef2f2" if c["cpi_chg"]>0 else "#f0fdf4"};color:{"#dc2626" if c["cpi_chg"]>0 else "#16a34a"};border:1px solid {"#fecaca" if c["cpi_chg"]>0 else "#bbf7d0"}">{chg_str(c["cpi_chg"])}</span>'
        rows += f"""<tr>
          <td>{c['flag']} {c['name']}</td>
          <td>${c['prev_cpi']:.2f}</td><td>${c['curr_cpi']:.2f}</td>
          <td class="{cls}">{badge}</td>
          <td class="{chg_class(c['curr_cpm']-c['prev_cpm'])}">${c['prev_cpm']:.2f}→${c['curr_cpm']:.2f}</td>
          <td class="{chg_class(c['curr_ipm']-c['prev_ipm'])}">{c['prev_ipm']:.2f}→{c['curr_ipm']:.2f}</td>
        </tr>"""
    return f"""
    <div style="padding:16px 20px 8px;">
      <div style="display:inline-block;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:20px;padding:4px 14px;font-size:12px;color:#16a34a;font-weight:600;margin-bottom:12px;">✓ 本周期无国家 CPI 上涨 ≥10%，整体表现良好</div>
      <div style="font-size:12px;color:#64748b;margin-bottom:12px;">最大上涨：IDN +5.21%（未达阈值）· 多国 CPI 大幅改善（KHM -17.9%、VNM -14.2%、MYS -10.8%）</div>
    </div>
    <div style="padding:0 20px 16px;">
      <table>
        <tr><th>国家</th><th>CPI 上期</th><th>CPI 本期</th><th>CPI 变化</th><th>CPM</th><th>IPM</th></tr>
        {rows}
      </table>
    </div>"""


def generate_html(d):
    pc = d["period_curr"]
    pp = d["period_prev"]

    # 1340 tab
    countries_1340 = d["p1340"]["countries"]
    cnt_1340 = len(countries_1340)
    body_1340 = "".join(render_country_block(c) for c in countries_1340)

    # 1180 tab
    body_1180 = render_1180_tab(d["p1180"])

    # 1233 tab
    countries_1233 = d["p1233"]["countries"]
    cnt_1233 = len(countries_1233)
    body_1233 = "".join(render_country_block(c) for c in countries_1233)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok 投放数据归因 | {pc}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 13px; background: #f4f6f9; color: #1a1a2e; }}
  .page {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

  /* Password gate */
  #pw-gate {{
    position: fixed; inset: 0; z-index: 9999;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    display: flex; align-items: center; justify-content: center;
  }}
  #pw-box {{
    background: white; border-radius: 16px; padding: 36px 40px; width: 320px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5); text-align: center;
  }}
  #pw-box .lock {{ font-size: 36px; margin-bottom: 12px; }}
  #pw-box h2 {{ font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }}
  #pw-box p {{ font-size: 12px; color: #94a3b8; margin-bottom: 20px; }}
  #pw-input {{
    width: 100%; padding: 11px 14px; border: 1.5px solid #e2e8f0; border-radius: 8px;
    font-size: 15px; letter-spacing: 4px; text-align: center; outline: none;
    transition: border-color 0.2s;
  }}
  #pw-input:focus {{ border-color: #6366f1; }}
  #pw-input.error {{ border-color: #ef4444; animation: shake 0.3s; }}
  #pw-err {{ font-size: 12px; color: #ef4444; margin-top: 8px; min-height: 16px; }}
  #pw-btn {{
    margin-top: 16px; width: 100%; padding: 11px; background: #6366f1;
    color: white; border: none; border-radius: 8px; font-size: 14px;
    font-weight: 600; cursor: pointer; transition: background 0.2s;
  }}
  #pw-btn:hover {{ background: #4f46e5; }}
  @keyframes shake {{
    0%,100% {{ transform: translateX(0); }}
    25% {{ transform: translateX(-6px); }}
    75% {{ transform: translateX(6px); }}
  }}

  .report-header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; border-radius: 12px; padding: 22px 28px; margin-bottom: 16px; }}
  .report-header h1 {{ font-size: 20px; font-weight: 700; }}
  .report-header .period {{ margin-top: 8px; font-size: 13px; opacity: 0.9; }}
  .report-header .period .curr {{ background: rgba(255,255,255,0.15); border-radius: 6px; padding: 3px 10px; margin-right: 8px; }}
  .report-header .period .prev {{ opacity: 0.6; font-size: 12px; }}
  .report-header .meta {{ margin-top: 8px; font-size: 11px; opacity: 0.55; }}

  /* Tabs */
  .tabs {{ display: flex; gap: 4px; margin-bottom: 16px; }}
  .tab-btn {{ padding: 9px 20px; border-radius: 8px 8px 0 0; border: 1px solid #e2e8f0; border-bottom: none; background: #f1f5f9; cursor: pointer; font-size: 13px; font-weight: 600; color: #64748b; transition: all 0.15s; }}
  .tab-btn:hover {{ background: #e8edf5; }}
  .tab-btn.active {{ background: white; color: #1e293b; border-color: #e2e8f0; }}
  .tab-btn .badge {{ display: inline-block; background: #ef4444; color: white; border-radius: 10px; padding: 1px 7px; font-size: 10px; margin-left: 5px; }}
  .tab-btn .badge.ok {{ background: #22c55e; }}
  .tab-content {{ display: none; background: white; border-radius: 0 12px 12px 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .tab-content.active {{ display: block; }}

  /* Product header */
  .product-header {{ padding: 14px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; gap: 10px; }}
  .product-id-badge {{ background: #1e293b; color: white; border-radius: 6px; padding: 3px 10px; font-size: 12px; font-weight: 700; }}
  .product-header h2 {{ font-size: 14px; font-weight: 600; color: #334155; }}
  .alert-count {{ margin-left: auto; font-size: 12px; background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; border-radius: 20px; padding: 2px 10px; }}

  /* Country block */
  .country-block {{ border-bottom: 1px solid #f1f5f9; }}
  .country-block:last-child {{ border-bottom: none; }}
  .country-header {{ padding: 12px 20px; display: flex; align-items: center; gap: 10px; }}
  .country-name {{ font-size: 14px; font-weight: 600; }}
  .cpi-badge {{ border-radius: 20px; padding: 3px 12px; font-size: 12px; font-weight: 700; }}
  .cpi-up {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}
  .attr-badge {{ border-radius: 20px; padding: 3px 10px; font-size: 11px; margin-left: 4px; }}
  .attr-media {{ background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }}
  .attr-creative {{ background: #fdf4ff; color: #9333ea; border: 1px solid #e9d5ff; }}
  .attr-both {{ background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }}

  .attr-section {{ padding: 10px 20px 0; }}
  .attr-bar-wrap {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .attr-bar {{ flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; display: flex; }}
  .attr-media-fill {{ background: #f97316; height: 100%; }}
  .attr-creative-fill {{ background: #a855f7; height: 100%; }}
  .attr-labels {{ font-size: 11px; color: #64748b; white-space: nowrap; }}
  .attr-labels span {{ margin-right: 12px; }}
  .attr-labels .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 3px; vertical-align: middle; }}

  .metrics-grid {{ display: flex; gap: 8px; padding: 0 20px 12px; flex-wrap: wrap; }}
  .metric-pill {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; min-width: 100px; }}
  .metric-pill .m-label {{ font-size: 10px; color: #94a3b8; text-transform: uppercase; }}
  .metric-pill .m-val {{ font-size: 12px; font-weight: 600; margin: 2px 0; }}
  .metric-pill .m-chg {{ font-size: 11px; }}
  .up {{ color: #dc2626; }} .down {{ color: #16a34a; }} .flat {{ color: #94a3b8; }}
  .chg-up {{ color: #dc2626; font-weight: 600; }}
  .chg-down {{ color: #16a34a; font-weight: 600; }}
  .chg-flat {{ color: #94a3b8; }}

  .table-section {{ padding: 0 20px 16px; }}
  .table-title {{ font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin: 10px 0 6px; display: flex; align-items: center; gap: 5px; }}
  .icon {{ width: 16px; height: 16px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; }}
  .icon-media {{ background: #fff7ed; color: #ea580c; }}
  .icon-creative {{ background: #fdf4ff; color: #9333ea; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #f8fafc; color: #64748b; font-size: 11px; font-weight: 600; padding: 7px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #fafbfd; }}
  .name-cell {{ max-width: 220px; overflow: hidden; text-overflow: ellipsis; }}
  .share-up {{ color: #f97316; font-weight: 600; }}
  .share-down {{ color: #64748b; }}
  .tag {{ font-size: 10px; border-radius: 3px; padding: 1px 5px; }}
  .tag-warn {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}
  .tag-ok {{ background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }}

  .conclusion {{ margin: 0 20px 16px; background: #f8fafc; border-left: 3px solid #6366f1; border-radius: 0 8px 8px 0; padding: 10px 14px; font-size: 12px; color: #334155; line-height: 1.6; }}
  .conclusion strong {{ color: #1e293b; }}

  .copy-btn {{ position: fixed; bottom: 24px; right: 24px; background: #6366f1; color: white; border: none; border-radius: 50px; padding: 11px 20px; font-size: 13px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px rgba(99,102,241,0.4); z-index: 100; }}
  .copy-btn:hover {{ background: #4f46e5; }}

  @media print {{ .copy-btn {{ display: none; }} }}
</style>
</head>
<body>

<!-- Password gate -->
<div id="pw-gate">
  <div id="pw-box">
    <div class="lock">🔒</div>
    <h2>TikTok 投放数据归因</h2>
    <p>请输入访问密码</p>
    <input id="pw-input" type="password" placeholder="密码" autocomplete="off"
           onkeydown="if(event.key==='Enter')checkPw()">
    <div id="pw-err"></div>
    <button id="pw-btn" onclick="checkPw()">进入</button>
  </div>
</div>

<div class="page">

<div class="report-header">
  <h1>TikTok 投放数据归因周报</h1>
  <div class="period">
    <span class="curr">📅 本期：{pc}</span>
    <span class="prev">对比上期：{pp}</span>
  </div>
  <div class="meta">账户 ly4znbvROd2ny068 · 筛选条件：CPI 上涨 ≥10% · 数据源：fact_dsp_core (gross_spend_usd) · 生成于 {d['generated_at']}</div>
</div>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('t1340')">1340 TikTok Lite <span class="badge">{cnt_1340}</span></button>
  <button class="tab-btn" onclick="switchTab('t1180')">1180 <span class="badge ok">✓</span></button>
  <button class="tab-btn" onclick="switchTab('t1233')">1233 <span class="badge">{cnt_1233}</span></button>
</div>

<!-- Tab 1340 -->
<div id="t1340" class="tab-content active">
  <div class="product-header">
    <span class="product-id-badge">1340</span>
    <h2>TikTok Lite · {d['p1340']['product_id']}</h2>
    <span class="alert-count">{cnt_1340} 个国家预警</span>
  </div>
  {body_1340}
</div>

<!-- Tab 1180 -->
<div id="t1180" class="tab-content">
  <div class="product-header">
    <span class="product-id-badge">1180</span>
    <h2>{d['p1180']['product_id']}</h2>
    <span style="margin-left:auto;font-size:12px;background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;border-radius:20px;padding:2px 10px;">✓ 无预警</span>
  </div>
  {body_1180}
</div>

<!-- Tab 1233 -->
<div id="t1233" class="tab-content">
  <div class="product-header">
    <span class="product-id-badge">1233</span>
    <h2>{d['p1233']['product_id']}</h2>
    <span class="alert-count">{cnt_1233} 个国家预警</span>
  </div>
  {body_1233}
</div>

</div>

<button class="copy-btn" onclick="copyText()">📋 复制摘要</button>

<script>
(function() {{
  if (sessionStorage.getItem('tt_auth') === '1') {{
    document.getElementById('pw-gate').style.display = 'none';
  }}
}})();

function checkPw() {{
  const val = document.getElementById('pw-input').value;
  if (val === 'TT') {{
    sessionStorage.setItem('tt_auth', '1');
    document.getElementById('pw-gate').style.display = 'none';
  }} else {{
    const inp = document.getElementById('pw-input');
    inp.classList.remove('error');
    void inp.offsetWidth;
    inp.classList.add('error');
    document.getElementById('pw-err').textContent = '密码错误，请重试';
    inp.value = '';
  }}
}}

function switchTab(id) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const idx = {{'t1340':0,'t1180':1,'t1233':2}};
  document.querySelectorAll('.tab-btn')[idx[id]].classList.add('active');
}}

function copyText() {{
  const lines = [
    'TikTok 投放数据归因周报',
    '本期：{pc} vs 上期：{pp}',
    '账户 ly4znbvROd2ny068 | CPI 上涨 ≥10%',
    '',
    '【产品 1340 TikTok Lite】预警 {cnt_1340} 个国家',
    '  BRA（巴西）: CPI +32.6%（$0.45→$0.59）',
    '  归因：媒体侧70%（CPM +21.7%）+ 创意侧30%（IPM -8.2%）',
    '  核心：SDK_MAX CPM +55.5%；install campaign CVR下降',
    '',
    '【产品 1180】✓ 无预警（IDN 最高 +5.2%，未达阈值）',
    '',
    '【产品 1233】预警 {cnt_1233} 个国家',
    '  PRY +31.2% | 创意侧83% | CVR -18.6%，DNU/0330 IPM崩塌',
    '  MOZ +20.1% | 创意侧97% | CTR -15.7pp，VUNGLE份额+7.5pp',
    '  DEU +19.2% | 创意侧100% | af_bs_conversion IPM -35%，Playable正常',
    '  IRQ +19.2% | 创意侧73% | 三campaign全部恶化，XIAOMI IPM -37%',
    '  NLD +18.9% | 创意侧100% | SDK_MAX效率+25%但份额缩减',
    '  SAU +18.1% | 媒体侧70% | pltv CPM +25.3%，唯一媒体侧驱动',
    '  BGD +10.1% | 各半 | VUNGLE CPM +23%，高效渠道缩量',
    '',
    '跨国共性：INMOBI/VUNGLE 在多国 CPM↑+IPM↓；高效渠道(SDK_MAX/FYBER)份额持续缩减',
  ];
  navigator.clipboard.writeText(lines.join('\\n')).then(() => {{
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '✓ 已复制';
    btn.style.background = '#22c55e';
    setTimeout(() => {{ btn.textContent = '📋 复制摘要'; btn.style.background = '#6366f1'; }}, 2000);
  }});
}}
</script>
</body>
</html>"""


def main():
    html = generate_html(REPORT_DATA)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ 报告已生成: {OUTPUT_FILE}")

    # Git push
    repo = str(REPO_DIR)
    period = REPORT_DATA["period_curr"].replace(" ", "").replace("~", "-")
    msg = f"report: {period} CPI归因报告"
    subprocess.run(["git", "-C", repo, "add", "index.html", "generate_tt_report.py"], check=False)
    r = subprocess.run(["git", "-C", repo, "commit", "-m", msg], capture_output=True, text=True)
    if "nothing to commit" in r.stdout:
        print("✓ 无变更，无需推送")
    else:
        subprocess.run(["git", "-C", repo, "push", "--set-upstream", "origin", "main"], check=False)
        print("✓ 已推送到 GitHub Pages")


if __name__ == "__main__":
    main()
