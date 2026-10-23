#!/usr/bin/env python3
"""麦门省钱凑单：本地凑单 + mock 算价。有 MCP 时由 Skill 换真实工具结果再调用同一套选择逻辑。"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "menu_sample.json"


@dataclass
class Item:
    code: str
    name: str
    category: str
    tags: list[str]
    price: float
    spicy: bool


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def filter_meals(
    meals: list[Item],
    *,
    no_spicy: bool,
    need_burger: bool,
    need_fries: bool,
    less_sugar: bool,
) -> list[Item]:
    out = []
    for m in meals:
        if no_spicy and m.spicy:
            continue
        if less_sugar and m.category == "饮料" and "无糖" not in m.tags and "少糖可选" not in m.tags:
            # 仍保留非饮料；饮料优先无糖，下面选品时再挑
            pass
        out.append(m)
    if need_burger:
        burgers = [m for m in out if "汉堡" in m.tags or m.category == "套餐"]
        if not burgers:
            return out
    if need_fries:
        # 套餐通常含薯，单品薯条作补充；不强制过滤掉其他
        pass
    return out


def pick_combo(
    meals: list[Item],
    *,
    people: int,
    budget: float,
    no_spicy: bool,
    prefer_less_sugar: bool,
) -> tuple[list[tuple[Item, int]], float, str]:
    """每人优先选一份非辣套餐；饮料在套餐外则选无糖。返回 (明细, 原价合计, 说明)。"""
    suites = sorted(
        [m for m in meals if m.category == "套餐" and not (no_spicy and m.spicy)],
        key=lambda x: x.price,
    )
    drinks = [m for m in meals if m.category == "饮料"]
    if prefer_less_sugar:
        drinks = sorted(
            drinks,
            key=lambda d: (0 if ("无糖" in d.tags or "少糖可选" in d.tags) else 1, d.price),
        )
    fries = [m for m in meals if "薯条" in m.tags]

    if not suites:
        return [], 0.0, "没有可用套餐（可能被忌口过滤）"

    # 贪心：尽量用最便宜套餐凑满人数，预算内再加中薯分享
    chosen: list[tuple[Item, int]] = []
    total = 0.0
    note_parts: list[str] = []

    unit = suites[0]
    if unit.price * people > budget:
        # 尝试更少人或提示
        max_n = int(budget // unit.price)
        if max_n <= 0:
            return [], 0.0, f"预算 ¥{budget:.0f} 买不起最低套餐「{unit.name}」(¥{unit.price:.0f})"
        chosen.append((unit, max_n))
        total = unit.price * max_n
        note_parts.append(f"预算不足 {people} 人，先按 {max_n} 人配置最低套餐")
    else:
        # 在预算内选尽量「完整」且总价接近预算（提升满足感），但仍 ≤ 预算
        # 从贵到便宜试，找不超过预算的最高人均套餐
        affordable = [s for s in suites if s.price * people <= budget]
        best = max(affordable, key=lambda s: s.price)
        chosen.append((best, people))
        total = best.price * people
        note_parts.append(f"每人 1 份「{best.name}」")

    remain = budget - total
    if fries and remain >= fries[0].price:
        # 加一份中薯分享
        chosen.append((fries[0], 1))
        total += fries[0].price
        note_parts.append(f"预算内加一份分享「{fries[0].name}」")

    return chosen, total, "；".join(note_parts)


def apply_best_coupon(subtotal: float, coupons: list[dict[str, Any]]) -> tuple[float, dict[str, Any] | None]:
    best = None
    best_pay = subtotal
    for c in coupons:
        if subtotal >= float(c.get("threshold", 0)):
            pay = max(0.0, subtotal - float(c["discount"]))
            if pay < best_pay:
                best_pay = pay
                best = c
    return best_pay, best


def format_report(
    store_name: str,
    people: int,
    budget: float,
    lines: list[tuple[Item, int]],
    subtotal: float,
    pay: float,
    coupon: dict[str, Any] | None,
    pick_note: str,
    mock: bool,
) -> str:
    rows = "\n".join(f"- {it.name} ×{qty}　¥{it.price * qty:.2f}" for it, qty in lines)
    saved = subtotal - pay
    coup = ("「" + coupon["name"] + "」") if coupon else "无可用券"
    mode = "本地 mock" if mock else "MCP"
    return f"""【麦门省钱凑单 · 草稿】（{mode}）
门店：{store_name}
人数 / 预算：{people} 人 / ¥{budget:.0f}
推荐组合：
{rows}
价格：原价 ¥{subtotal:.2f} → 优惠券 {coup} → 应付 ¥{pay:.2f}（剩余预算 ¥{max(0, budget - pay):.2f}）
省钱说明：相对原价节省 ¥{saved:.2f}。{pick_note}
状态：仅草稿，未创建订单、未支付。
"""


def run(budget: float, people: int, no_spicy: bool, less_sugar: bool, need_fries: bool) -> str:
    data = load_fixture()
    meals = [
        Item(
            code=m["code"],
            name=m["name"],
            category=m["category"],
            tags=list(m.get("tags") or []),
            price=float(m["price"]),
            spicy=bool(m.get("spicy")),
        )
        for m in data["meals"]
    ]
    meals = filter_meals(
        meals, no_spicy=no_spicy, need_burger=True, need_fries=need_fries, less_sugar=less_sugar
    )
    lines, subtotal, note = pick_combo(
        meals, people=people, budget=budget, no_spicy=no_spicy, prefer_less_sugar=less_sugar
    )
    if not lines:
        return f"无法凑单：{note}"
    pay, coupon = apply_best_coupon(subtotal, data.get("coupons") or [])
    if pay > budget:
        return (
            format_report(
                data["store"]["name"], people, budget, lines, subtotal, pay, coupon, note, True
            )
            + f"\n注意：优惠后仍超预算 ¥{pay - budget:.2f}，请提高预算或减少人数。"
        )
    return format_report(
        data["store"]["name"], people, budget, lines, subtotal, pay, coupon, note, True
    )


def main() -> None:
    p = argparse.ArgumentParser(description="麦门省钱凑单助手 · 本地演示")
    p.add_argument("--budget", type=float, default=80)
    p.add_argument("--people", type=int, default=2)
    p.add_argument("--no-spicy", action="store_true", default=True)
    p.add_argument("--allow-spicy", action="store_true", help="允许辣")
    p.add_argument("--less-sugar", action="store_true", default=True)
    p.add_argument("--fries", action="store_true", default=True)
    args = p.parse_args()
    no_spicy = not args.allow_spicy
    print(run(args.budget, args.people, no_spicy, args.less_sugar, args.fries))


if __name__ == "__main__":
    main()
