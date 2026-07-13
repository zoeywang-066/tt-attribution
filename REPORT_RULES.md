# TT 数据更新报告规则

本项目固定维护两个报告：

- 单周报：`index.html`，每周一更新上上周日到上周六，对比前一个 7 天。
- 双周报：`biweekly.html`，每双周的周一更新。由于 sandbox 数据通常为 T-2，周期以最新可用周六为结束日，向前取 14 天（周日到周六），对比前一个 14 天。

## 触发逻辑

单周报和双周报使用同一套触发逻辑：

- 统计粒度：国家 / OS / app id。
- 指标：BI CPI 或 DNU。
- 触发条件：BI CPI 或 DNU 在统计周期内相对对比周期波动超过 10%，上涨和下降都触发。
- Benchmark：优先使用 `ads-bpd-guard-sandbox.sherry` 沙盒表作为波动和大盘 benchmark。
- 明细归因：使用 Moloco BQ / `ads-bpd-guard-china.athena` 明细表拆解 campaign、投放事件、媒体、creative、bundle。

## 归因输出要求

不要只罗列数字。每个触发国家必须给一条完整、可直接复制给客户的一句话总结：

> 这个国家在本周期 BI CPI / DNU 波动的主要原因是：某个投放事件或 campaign 成本上升 / 降量，或某些 top 媒体 CPM/CPI 上涨，或某个创意组/版位衰败，或 bundle 子渠道结构变化。

结论下面再列数据证据：

- BI CPI / DNU 的变化幅度。
- 国家预算/消耗变化：DNU 波动必须解释预算是否调整、消耗是否上升/下降，以及 CPI 成本变化是否导致同预算获量减少或增加。
- 主要 campaign / 投放事件的消耗占比、CPI、变化。
- top 媒体的占比变化、CPM、CPI、IPM。
- top creative / creative format 的 CPI、IPM、占比变化。
- top bundle id / publisher 的占比变化、CPI、CPM、IPM。
- 游戏行业和非游戏行业的大盘 CPM / CPI benchmark 对比。

## 优化建议输出要求

每个触发国家要给可执行动作，优先按以下顺序：

- 降低高成本事件或高成本 campaign 的预算。
- 如果 DNU 下滑来自国家预算下降，需要明确是主动预算调整还是成本上升导致消耗转移；如果 DNU 下滑来自 CPI 上涨，需要优先压低高成本流量。
- 屏蔽或降量高成本媒体 / exchange / bundle。
- 移除高 CPI、IPM 衰退的创意组。
- 补充测试新创意，特别是当前主力版位疲劳时。
- 若大盘也同步上涨，沟通口径要标注“行业大盘上行”，避免把全部原因归到投放操作。

## 页面结构

- 单周报保留当前客户周报页。
- 双周报保留两个 tab：整体波动纵览、归因详情。
- 每个归因详情块必须先展示“结论 + 主要原因判断”，然后才展示明细表。
