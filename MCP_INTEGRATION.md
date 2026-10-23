# MCP 集成说明：麦门省钱凑单助手

## MCP Server

| 项 | 值 |
|---|---|
| Server 名称 | `mcd-mcp`（麦当劳中国官方托管） |
| 接入地址 | `https://mcp.mcd.cn` |
| 协议 | Streamable HTTP / JSON-RPC 2.0 |
| 鉴权 | `Authorization: Bearer <MCP_TOKEN>`（Token 仅放环境变量或仓库外 `.secrets/`，永不提交） |
| 文档 | https://open.mcd.cn/mcp/doc 、https://github.com/M-China/mcd-mcp-server |

## 实机已验证（只读）

- `scripts/live_smoke.py`：`initialize` → `tools/list` → `tools/call` `list-nutrition-foods`
- 结果 JSON 落盘 `/tmp/mcd-smoke-*.json`；脚本**永不打印 Token**
- 演示与默认 Skill **禁止**调用：`create-order`、`mall-create-order`、`cancel-order`、`auto-bind-coupons`、`draw-lottery` 等写操作

## 本 Skill 使用的 Tools（官方名）

| Tool | 用途 |
|---|---|
| `now-time-info` | 判断早餐/正餐时段 |
| `query-nearby-stores` | 到店：按地址查可点餐门店 |
| `query-meals` | 门店可售菜单（需先有门店；`orderType=1` 到店 / `2` 外送） |
| `query-meal-detail` | 套餐组成与可替换项 |
| `list-nutrition-foods` | 按热量/营养过滤（**无需门店**，smoke 首选） |
| `campaign-calendar` | 当月活动，解释优惠 |
| `query-store-coupons` / `query-my-coupons` / `available-coupons` | 可用券 / 卡包券 / 可领券（只读展示） |
| `calculate-price` | 对草稿算金额、配送费、优惠与应付 |

## Safe 调用流程（演示默认停在草稿）

```
用户：预算 B、人数 N、偏好 P、地址/取餐方式
  → now-time-info
  → query-nearby-stores（或用户已指定 store）
  → query-meals(store, orderType)
  → （可选）query-meal-detail / list-nutrition-foods 按 P 过滤
  → query-store-coupons / query-my-coupons（只读）
  → campaign-calendar（解释活动）
  → 本地凑单 src/budget_combo.py
  → calculate-price(草稿)
  → 输出推荐与省钱说明 · 停止
       （用户明确确认后，才允许人工触发下单；本仓库演示不触发）
```

无 Token：用 `fixtures/menu_sample.json` mock 同一输出模板。

## 业务价值

- 控预算、讲清楚省在哪；基于官方 MCP，换门店/时段可复用。
