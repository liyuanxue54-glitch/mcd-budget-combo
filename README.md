# 麦门省钱凑单助手

一句话：输入预算、人数和口味偏好，用麦当劳 MCP 查菜单与优惠，自动凑出最划算的可下单组合并说明省了多少。

## 这是什么

WorkBuddy Skill。面向「想吃麦当劳但怕超预算」的用户：给定人均/总预算、人数、偏好（如少辣、要薯条、不要甜品），Skill 会：

1. 查附近门店与可售菜单  
2. 拉取门店券 / 活动日历（有 Token 时）  
3. 在预算内组合套餐与单品  
4. 用 `calculate-price` 报价并对比「无券原价」解释省钱点  
5. **只输出购物车草稿，不自动支付**

无 MCP Token 时走本地 `fixtures/` mock，保证可演示。

## 目标用户

- 学生党 / 打工人：固定预算点麦当劳  
- 麦门爱好者：想用满券、活动价凑一单  
- 参赛演示：≤3 分钟讲清「查菜 → 凑单 → 省钱说明」

## 安装（WorkBuddy）

1. 申请 Token：见仓库上级 `../TOKEN_SETUP.md` 或 https://open.mcd.cn/mcp  
2. 在 WorkBuddy 配置并启用 `mcd-mcp` 连接器  
3. 将本仓库 `skills/mcd-budget-combo/` 导入为自定义 Skill（或把 `SKILL.md` 内容粘贴为专家技能说明）  
4. 可选：把本仓库克隆到本机，便于对照 `USAGE.md` 录屏  

## 快速用法

在 WorkBuddy 对话中说：

> 用麦门省钱凑单助手：预算一共 80 元，2 人，要汉堡+薯条，少辣，外送或到店都行，只要草稿不要下单。

Skill 会返回：推荐组合、预估应付、对比原价、省了多少、以及「确认后再下单」的提示。

更完整演示脚本见 [USAGE.md](./USAGE.md)。

## 仓库结构

```
README.md
CONTEST_DECLARATION.md   # 官方参赛声明（内容不可改）
MCP_INTEGRATION.md
workbuddy.md
USAGE.md
skills/mcd-budget-combo/SKILL.md
src/budget_combo.py      # 凑单逻辑（mock / 真实结构共用）
fixtures/menu_sample.json
```

## 安全与合规

- 不提交真实 Token；配置只用环境变量占位符  
- 默认禁止调用 `create-order`  
- 价格与供应以麦当劳官方实时结果为准；本工具输出仅供参考  

## 许可

参赛作品，仅供学习与演示。非麦当劳官方产品。
