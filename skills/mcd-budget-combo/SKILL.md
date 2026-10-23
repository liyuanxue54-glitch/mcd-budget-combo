---
name: mcd-budget-combo
description: >-
  当用户要按预算凑麦当劳套餐/一单、省钱点餐、满券凑单，或提到「麦门省钱凑单助手」时使用。
  调用麦当劳 MCP（mcd-mcp）查门店、菜单、优惠并 calculate-price；默认只出购物车草稿，不下单支付。
---

# 麦门省钱凑单助手

用麦当劳中国 MCP 帮用户在**硬预算**内凑出可下单组合，并讲清省了多少。面向 WorkBuddy。

## 硬规则

1. **默认禁止下单**：不要调用 `create-order` / `mall-create-order`。只查菜单、券、算价，输出「购物车草稿」。
2. **预算是硬约束**：推荐方案应付总额必须 ≤ 用户预算；做不到就说明差多少，给「放开预算」或「减少人数/品类」选项。
3. **中文对用户说话**：商品名、省钱说明、确认话术用中文。
4. **无 Token / 工具不可用**：读取本仓库 `fixtures/menu_sample.json`，用同一套凑单逻辑演示，并明确告知「当前为本地 mock」。
5. **不编造价格**：真实模式只采用 MCP 返回或 `calculate-price` 结果；mock 只用 fixtures 里的价。

## 需要向用户确认的输入（缺什么问什么，一次问齐）

- 总预算（元）或人均预算 × 人数  
- 人数  
- 偏好：忌口（如少辣）、必点/不要的品类、饮料糖分  
- 取餐方式：到店 / 外送（外送需地址或已有配送地址）  
- 是否允许「一键领券」`auto-bind-coupons`（默认否，只展示可领券）

## 工具调用顺序（有 mcd-mcp 时）

1. `now-time-info` — 判断时段  
2. `query-nearby-stores` 或用户指定门店 — 选定 `store`  
3. `query-meals` — 可售列表  
4. 按需 `query-meal-detail`、`list-nutrition-foods` 过滤偏好  
5. `query-store-coupons` / `query-my-coupons`（只读）；可选 `campaign-calendar`  
6. 用本地逻辑或脚本 `src/budget_combo.py` 生成候选草稿（每人尽量「主食+小食/饮料」完整一餐）  
7. `calculate-price` 验证总额；若超预算则减配/换低价项再算，最多 3 轮  
8. 输出推荐：清单、原价、优惠、应付、省钱点、**未下单**声明  

## 输出模板（对用户）

```text
【麦门省钱凑单 · 草稿】
门店：…
人数 / 预算：N 人 / B 元
推荐组合：
- …
价格：原价 ¥A → 优惠 ¥C → 应付 ¥P（预算内还剩 ¥R）
省钱说明：…
状态：仅草稿，未创建订单、未支付。需要我按此单去下单时请明确说「确认下单」（本演示环境仍建议你在官方 App 完成支付）。
```

## 失败与降级

- MCP 401/无连接器 → mock + 提示配置 Token（见 TOKEN_SETUP）  
- 菜单为空 → 换门店或提示非营业时段  
- 券与商品不匹配 → 去掉该券重算，不要假装已优惠  

## 实现参考

- 凑单算法：`src/budget_combo.py`  
- Mock 数据：`fixtures/menu_sample.json`  
- 集成说明：仓库根目录 `MCP_INTEGRATION.md`
