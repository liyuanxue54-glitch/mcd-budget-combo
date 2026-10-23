# WorkBuddy 开发对话记录 · 麦门省钱凑单助手

> 导出说明：以下为使用 WorkBuddy + 麦当劳 MCP（mcd-mcp）开发本 Skill 时的关键对话摘要，用于参赛核验。演示默认不下单。

---

## 回合 1 — 立项

**用户：**  
我想做一个 WorkBuddy Skill 参加 1024 用餐赛道和麦当劳程序员创意开发大赛：按预算凑最划算的麦当劳一单，要讲清楚省了多少。不要自动付款。

**WorkBuddy：**  
可以。建议名称「麦门省钱凑单助手」。先确认你已在连接器里配置 `mcd-mcp`（`https://mcp.mcd.cn` + Bearer Token）。Skill 流程：`query-nearby-stores` → `query-meals` → 读券 → 本地凑单 → `calculate-price`，禁止默认调用 `create-order`。我先写 `SKILL.md` 和 `MCP_INTEGRATION.md` 骨架。

---

## 回合 2 — 接 MCP

**用户：**  
Token 还在申请，先用 mock 把逻辑跑通，工具名要和官方一致。

**WorkBuddy：**  
已按官方文档对齐工具名：`now-time-info`、`query-nearby-stores`、`query-meals`、`query-meal-detail`、`list-nutrition-foods`、`campaign-calendar`、`query-store-coupons`、`query-my-coupons`、`available-coupons`、`calculate-price`。本地 `fixtures/menu_sample.json` + `src/budget_combo.py` 可在无 Token 时演示同一输出模板。

（模拟工具调用）

```text
→ now-time-info
← 当前为正餐时段
→ query-meals (mock)
← 返回套餐/小食/饮料列表
→ calculate-price (mock: 满60减10)
← 应付 67 元
```

**用户：**  
预算 80、2 人、少辣、要薯条，输出看看。

**WorkBuddy：**  
【麦门省钱凑单 · 草稿】双层吉士汉堡套餐×2 + 中薯×1，原价 77，券后 67，省 10。仅草稿未下单。

---

## 回合 3 — 打磨 Skill 话术

**用户：**  
对用户全中文，超预算要直接说做不到，别硬推。

**WorkBuddy：**  
已写入 SKILL：预算硬约束；超预算报告差额并给「加预算 / 减人数」选项；领券 `auto-bind-coupons` 默认关闭，需用户明确同意。

---

## 回合 4 — 参赛材料

**用户：**  
补上官方 CONTEST_DECLARATION、README、USAGE 录屏脚本，以及 workbuddy 对话导出。

**WorkBuddy：**  
已从官方仓库复制 `CONTEST_DECLARATION.md`（内容未改）。`USAGE.md` 控制在 3 分钟内可录完。仓库无 Token。可以推 Public GitHub 后按标准格式发报名 Issue。

---

---

## 回合 5 — 实机 MCP 冒烟

**用户：**  
Token 已就绪，跑一遍只读 live smoke，确认工具名和营养列表可用。

**WorkBuddy：**  
已用 `scripts/live_smoke.py` 对 `https://mcp.mcd.cn` 完成：`initialize` → `tools/list` → `list-nutrition-foods`（无需门店）。结果写入 `/tmp/mcd-smoke-*.json`。**Live MCP verified**（只读）。演示仍不调用 `create-order` / `mall-create-order` / `cancel-order` / `auto-bind-coupons` / `draw-lottery`。Token 仅存仓库外 `.secrets/`，未写入本对话、未提交。

---

## 验收自检

- [x] 调用链只读 + 算价  
- [x] 中文输出模板  
- [x] mock 可演示  
- [x] **Live MCP verified**（tools/list + list-nutrition-foods）  
- [x] 声明文件齐全；无 Token 进仓  
