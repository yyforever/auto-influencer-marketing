## LangGraph Agent 设计蓝图

> 以「七阶段达人营销流程」为主线，严格落实*LangGraph 高阶设计指南*中的 **State／Node／Edge／Graph／HITL／并行** 原则。所有元素均用 LangGraph 原语（`Graph / SubGraph / Node / Edge / State`）描述，便于直接落地。

---

### 0. 顶层视图

```
InfluencerMarketingGraph
│
├─ Phase1_Strategy      （子图）
├─ Phase2_Discovery     （子图，可并行）
├─ Phase3_Outreach      （子图）
├─ Phase4_Cocreation    （子图）
├─ Phase5_PublishBoost  （子图，并行）
├─ Phase6_MonitorOpt    （子图，循环）
└─ Phase7_SettleArchive （子图）
```

* 所有子图最终回流至 `END` 节点并输出 `campaign_report`。
* 关键风险点（预算超标、合规审核）前后放置 **HITL Interrupt** 节点。
* 每个子图对外暴露为 **Toolified Agent**，可被外部系统或其他节点复用。

---

### 1. 全局 State 设计（最小、类型安全、可归约）

```python
class CampaignState(TypedDict, total=False):
    objective: str                 # 单次/年度目标
    budget: float                  # 可用预算
    kpi: dict[str, float]          # CPM / CPA / ROAS …
    candidates: list[Creator]      # 达人池
    contracts: list[Contract]
    scripts: list[Script]
    posts: list[PostLink]
    performance: dict[str, Metric] # 实时指标
    settlements: list[Invoice]
    phase: Literal[1,2,3,4,5,6,7]  # 当前阶段
    logs: list[str]                # 事件日志
```

* **不可变写法**：节点返回 `{ "budget": new_value }` 之类增量 dict。
* `candidates`, `logs` 字段加 `Annotated[..., operator.add]` 归并策略，方便并行分支 Fan‑in。
* 所有大型原始 API 响应仅保留 `id/score/url`，避免状态爆炸。

---

### 2. 子图与关键节点

#### Phase 1 – Strategy (`Phase1_Strategy`)

| Node               | 职责                                 | 输入 → 输出                              | 说明                    |
| ------------------ | ---------------------------------- | ------------------------------------ | --------------------- |
| `init_goal`        | 解析 Brief，生成 `objective/kpi`        | user\_brief → objective,kpi          | 可缓存                   |
| `budget_predictor` | **Tool** 调用 Influencity API 预测 ROI | objective,kpi → budget               | 幂等，可 Node‑level Cache |
| `HITL_review`      | 人审确认目标与预算                          | objective,kpi,budget → pass / revise | HITL Interrupt        |
| `finish_p1`        | 记录日志并流向 Phase 2                    | … → phase=2                          |                       |

固定边：`init_goal → budget_predictor → HITL_review → finish_p1`

---

#### Phase 2 – Discovery (`Phase2_Discovery`)

> **并行 Fan‑out**：多路候选池并行搜集后在 `merge_candidates` 汇总。

| Node                 | 职责                    | 特点                               |
| -------------------- | --------------------- | -------------------------------- |
| `search_by_topic`    | 调用 Influencity 搜索主题达人 |                                  |
| `search_by_audience` | 受众画像检索                |                                  |
| `lookalike`          | Look‑alike 扩散         |                                  |
| `fraud_check`        | 反欺诈过滤（僵尸粉检测）          |                                  |
| `merge_candidates`   | **聚合节点**，合并并去重        | 使用 Reducer，对候选列表做 `operator.add` |
| `rank_score`         | LLM 评分 + 规则打分         |                                  |
| `finish_p2`          | 写入 `phase=3`          |                                  |

边：

* `ENTRY → {search_*}`（并行）
* `{search_*} → fraud_check → merge_candidates → rank_score → finish_p2`

---

#### Phase 3 – Outreach (`Phase3_Outreach`)

| Node                   | 职责                                   | 备注   |
| ---------------------- | ------------------------------------ | ---- |
| `generate_email`       | LLM 写冷启动邮件                           |      |
| `send_and_track`       | **Tool**：邮件序列 API，未回 7 天自动 follow‑up |      |
| `negotiate_contract`   | 若收到报价，生成合同草案                         |      |
| `HITL_contract_review` | 法务审核合同                               | HITL |
| `finish_p3`            | phase=4                              |      |

条件边：

* `send_and_track` → 根据响应分支 `negotiate_contract` 或回到 `generate_email`（循环上限 N 次）
* `negotiate_contract → HITL_contract_review → finish_p3`

---

#### Phase 4 – Co‑creation (`Phase4_Cocreation`)

| Node              | 职责                    |
| ----------------- | --------------------- |
| `draft_script`    | LLM+Brief 产脚本         |
| `compliance_scan` | **Tool**：生成式 AI 检查违禁词 |
| `HITL_legal`      | 人审二审                  |
| `finish_p4`       | phase=5               |

* 若 `compliance_scan` 失败 → 回 `draft_script`
* 每次循环计数写入状态，Watchdog 防无限回环。

---

#### Phase 5 – Publish & Boost (`Phase5_PublishBoost`)

> **并行**处理多平台发布，节点声明 `deferred=True`，待所有平台完成后再聚合。

| Node                   | 职责            |
| ---------------------- | ------------- |
| `schedule_post_TikTok` |               |
| `schedule_post_XHS`    |               |
| `schedule_post_IG`     |               |
| `wait_all_publish`     | Deferred Node |
| `finish_p5`            |               |

---

#### Phase 6 – Monitor & Optimize (`Phase6_MonitorOpt`)

| Node                | 职责                       | 类型   |
| ------------------- | ------------------------ | ---- |
| `pull_metrics`      | Dashboard API 拉数据        | 循环节点 |
| `detect_winner`     | 找爆款并决定追加预算               |      |
| `adjust_budget`     | **Tool** 更新预算            |      |
| `HITL_budget_guard` | 人工大额预算审批                 | HITL |
| `loop_or_finish`    | 若满足 KPI → phase=7，否则继续循环 |      |

Edge：在 `loop_or_finish` 内设置最大迭代或达标即退出。

---

#### Phase 7 – Settle & Archive (`Phase7_SettleArchive`)

| Node                    | 职责                   |
| ----------------------- | -------------------- |
| `generate_invoice_pool` | 汇总佣金                 |
| `bulk_payment`          | **Tool** 打款          |
| `archive_assets`        | 云存储归档素材              |
| `update_creator_db`     | 更新红人画像               |
| `END`                   | 输出 `campaign_report` |

---

### 3. Toolified 子 Agent 说明

| 子图                 | 对外暴露为                        | 复用场景       |
| ------------------ | ---------------------------- | ---------- |
| Phase2\_Discovery  | `discover_creators_tool`     | 其他团队快速拉达人池 |
| Phase3\_Outreach   | `outreach_tool`              | 不同品牌邮件沟通   |
| Phase6\_MonitorOpt | `performance_dashboard_tool` | 跨项目统一监测    |

* 每个 Tool 在定义时指明 `input_schema` / `output_schema`，保持松耦合。
* **幂等**：对同一输入参数启用缓存；Dashboard Tool 对近实时请求禁用缓存。

---

### 4. 关键并行与循环模式

* **Fan‑out**：Phase 2 多路搜索；Phase 5 多平台发布。
* **Fan‑in**：`merge_candidates`, `wait_all_publish`。
* **循环**：Phase 3 邮件追踪，Phase 6 数据监测。
* 所有循环节点均携带 `iteration` 计数并有上限，防止“循环无终止”陷阱。

---

### 5. Human‑in‑the‑Loop 触点

| 环节     | 节点                     | 目的    |
| ------ | ---------------------- | ----- |
| 目标预算确认 | `HITL_review`          | 战略正确性 |
| 合同审核   | `HITL_contract_review` | 合规与风险 |
| 法务二审   | `HITL_legal`           | 内容安全  |
| 预算追加   | `HITL_budget_guard`    | 财务把控  |

每个 HITL 节点返回 `approve/revise/reject`，边路由据此跳转。

---

### 6. 设计后的自我反思（对照指南）

| 指南要点                | 落实情况                        | 尚可改进                           |
| ------------------- | --------------------------- | ------------------------------ |
| **最小 State**        | 仅存业务关键字段，列表字段显式 Reducer     | 未来可按阶段切分子状态减少跨阶段耦合             |
| **单一职责 Node**       | 每个 Node 聚焦单功能；复杂逻辑拆子图       | 若脚本生成逻辑复杂，可再拆“草案‑润色‑校验”子图      |
| **并行 + Aggregator** | Phase 2/5 并行，多用 Deferred 聚合 | 考虑 Map‑Reduce 优化批量评论分析         |
| **HITL 刹车**         | 4 处高风险节点加入 Interrupt        | 可加可选“旁观模式”以收集数据、减少人工干预         |
| **幂等/缓存**           | 读 API 节点默认缓存；循环节点幂等         | 后续引入外部 KV 缓存，便于横向扩容            |
| **条件 Edge**         | 邮件响应、KPI 达成均用条件边            | 若 LLM 决策边复杂，可升级为专用决策子图         |
| **状态机心态**           | 整体先显式编排，再逐步 Agentic         | 后期可让 `detect_winner` 变成自适应策略节点 |

> **结论**：设计遵循「可观察的状态机」哲学，先用显式工作流保证可控，再通过并行、工具化、HITL 等模块化能力提升自治度与扩展性；核心数据流保持轻量且可归约，为后续性能优化留足空间。
