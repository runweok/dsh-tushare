#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tsq.py — Tushare 个股研究速查 CLI（dsh-tushare 技能随包脚本）

设计目标：把「环境检查 → token 解析 → 现场写 Python → 字段试错 → 手写格式化」
五步并成一条命令。输出统一为紧凑 markdown 表（中文按 2 格宽对齐），带数据时点标注。

子命令（对齐个股研究默认路由：westock 主查 + tushare 三件套补位）：
  tsq.py smoke                     冒烟：交易日历取几行，验证 token/环境
  tsq.py lhb <YYYYMMDD>            龙虎榜：上榜个股 + 营业部明细（必传 trade_date，逐日查）
  tsq.py dv <code> [--days N]      估值交叉：daily_basic（PE/PB/市值/换手）
  tsq.py mf <code> [--days N]      大单结构：moneyflow，联动 daily 补涨跌幅
  tsq.py fina <code> [--limit N]   财务复核：fina_indicator 最近报告期快照
  tsq.py daily <code> [--days N]   基础日线行情

约定：
  - code 支持 600519 / 600519.SH（自动补交易所后缀：6→SH，0/3→SZ，4/8/920→BJ）
  - 全部列选择走「白名单 + 存在性过滤 + 本地补算」，上游缺列不报错、能算则算。
    已知坑见 SKILL.md「已知接口坑」节，本脚本已内置规避：
      * top_list 当前积分必传 trade_date（本脚本逐日查，不支持区间）
      * moneyflow 无 pct_change 列（从 daily 联动补涨跌幅；净流入列缺则本地按买-卖计算）
      * fina_indicator 自选 fields 不返回 end_type（按 end_date 推断报告期类型）
  - 单位显示统一换算为「亿」（上游元/万元，换算仅影响显示，CSV 落盘保留原始值）
  - 退出码：0 成功 / 2 参数错误 / 3 权限或积分不足 / 4 网络或服务错误
  - --csv 路径 可同时落盘 CSV；--debug 打印原始异常

零第三方依赖（仅标准库 + tushare/pandas，后者为技能运行前提）。
"""

import argparse
import datetime
import os
import pathlib
import sys
import unicodedata

EXIT_OK, EXIT_ARGS, EXIT_PERM, EXIT_NET = 0, 2, 3, 4

TOKEN_CHAIN = [
    ("环境变量 TUSHARE_TOKEN", lambda: os.getenv("TUSHARE_TOKEN", "").strip()),
    ("~/.dsh/skills/tushare-data/token",
     lambda: _read(pathlib.Path.home() / ".dsh" / "skills" / "tushare-data" / "token")),
    ("~/.tushare/token", lambda: _read(pathlib.Path.home() / ".tushare" / "token")),
]


def _read(p):
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def resolve_token():
    """token 三路解析：环境变量 → 技能目录 → ~/.tushare。返回 (token, 来源)。"""
    for name, fn in TOKEN_CHAIN:
        v = fn()
        if v:
            return v, name
    try:
        import tushare as ts
        v = ts.get_token()
        if v:
            return v, "tushare 本地配置 ts.get_token()"
    except Exception:
        pass
    _die("token 未配置。设置：/tushare-token <token>，或 export TUSHARE_TOKEN=<token>", EXIT_ARGS)


def get_pro():
    token, src = resolve_token()
    try:
        import tushare as ts
        return ts.pro_api(token), src
    except Exception as e:
        _die(f"tushare 初始化失败：{e}（pip install tushare）", EXIT_NET)


def _die(msg, code):
    print(f"[tsq] {msg}", file=sys.stderr)
    sys.exit(code)


def norm_code(s):
    """600519 → 600519.SH；已带后缀则原样校验。"""
    s = s.strip().upper()
    if "." in s:
        return s
    if len(s) != 6 or not s.isdigit():
        _die(f"无法解析代码：{s}（示例：600519 或 600519.SH）", EXIT_ARGS)
    if s[0] == "6":
        return s + ".SH"
    if s[0] in "03":
        return s + ".SZ"
    if s[0] in "48" or s.startswith("92"):
        return s + ".BJ"
    _die(f"无法按首位推断交易所：{s}（请写全：600519.SH 形式）", EXIT_ARGS)


# ---------------- 显示层：中文宽度对齐的紧凑 markdown 表 ----------------

def disp_w(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in str(s))


def pad(s, w):
    return str(s) + " " * max(0, w - disp_w(s))


def truncate(s, limit):
    s = str(s)
    if disp_w(s) <= limit:
        return s
    out, w = "", 0
    for c in s:
        cw = 2 if unicodedata.east_asian_width(c) in ("F", "W") else 1
        if w + cw > limit - 1:
            return out + "…"
        out += c
        w += cw
    return out


def md_table(rows, headers=None, limits=None):
    """rows: list[dict]；headers 缺省取首行键序；limits: {列: 截断宽}。"""
    if not rows:
        return "（空表——注意区分非交易日/未上市/无权限，见 SKILL.md 数据质量规则）"
    headers = headers or list(rows[0].keys())
    limits = limits or {}
    widths = {
        h: min(limits.get(h, 28),
               max(disp_w(h), max(disp_w(truncate(r.get(h, ""), limits.get(h, 28))) for r in rows)))
        for h in headers
    }
    fmt = lambda r: "|" + "|".join(
        " " + pad(truncate(r.get(h, ""), widths[h]), widths[h]) + " " for h in headers) + "|"
    return "\n".join(
        [fmt({h: h for h in headers}),
         "|" + "|".join("-" * (widths[h] + 2) for h in headers) + "|"]
        + [fmt(r) for r in rows])


def pick(df, want_map):
    """白名单 + 存在性过滤 → list[dict]。上游缺列自动跳过，绝不 KeyError。"""
    out = []
    for _, row in df.iterrows():
        d = {}
        for col, label in want_map.items():
            if col not in df.columns:
                continue
            v = row[col]
            if hasattr(v, "item"):
                v = v.item()
            d[label] = "" if v is None or (isinstance(v, float) and v != v) else v
        out.append(d)
    return out


def scale(df, cols, factor):
    """就地数值换算（显示单位归一），缺列自动跳过。"""
    for c in cols:
        if c in df.columns:
            df[c] = (df[c] / factor).round(2)
    return df


def num(v):
    """数字去掉多余小数尾零，便于对齐阅读。"""
    if isinstance(v, float):
        return f"{v:g}"
    return v


def drop_empty_cols(rows):
    """剔除整列皆空的展示列（上游缺列时不留空位）。"""
    if not rows:
        return rows
    keys = list(rows[0].keys())
    keep = [k for k in keys if any(r.get(k) not in ("", None) for r in rows)]
    return [{k: r[k] for k in keep} for r in rows]


# ---------------- 数据层 ----------------

def date_window(days):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days * 2)  # 自然日换交易日余量
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


# ---------------- 子命令 ----------------

def cmd_smoke(args):
    pro, src = get_pro()
    start, end = date_window(5)
    df = pro.trade_cal(exchange="SSE", start_date=start, end_date=end)
    rows = pick(df, {"cal_date": "日期", "is_open": "开市(1/0)"})
    print(f"## tushare 冒烟 · token 来源: {src} · 今天 {datetime.date.today().strftime('%Y%m%d')}")
    print(md_table(list(reversed(rows)), ["日期", "开市(1/0)"], {"日期": 10}))


def cmd_lhb(args):
    pro, src = get_pro()
    d = args.date
    if len(d) != 8 or not d.isdigit():
        _die("龙虎榜日期格式须为 YYYYMMDD（必传 trade_date，逐日查——当前积分不支持区间）", EXIT_ARGS)
    note = ""
    if d == datetime.date.today().strftime("%Y%m%d") and datetime.datetime.now().hour < 17:
        note = "⚠️ 当日龙虎榜约 17:00 后披露，早于披露时点大概率返回空（数据时效闸门）"
    tl = pro.top_list(trade_date=d)
    if tl is None or tl.empty:
        print(f"## 龙虎榜 {d} · 数据时点: 盘后披露（约17:00后）")
        print("（当日无上榜数据：可能非交易日、无异动、或未到披露时点）")
        if note:
            print(note)
        return
    # top_list/top_inst 金额上游单位为元 → 统一换算为亿
    scale(tl, ["net_amount", "l_amount", "amount", "l_buy", "l_sell"], 1e8)
    rows = pick(tl, {
        "ts_code": "代码", "name": "名称", "close": "收盘", "pct_change": "涨跌%",
        "net_amount": "榜内净买(亿)", "l_amount": "榜内成交(亿)",
        "amount_rate": "榜内占比%",
    })
    print(f"## 龙虎榜上榜个股 {d} · 数据时点: 盘后披露 · 共 {len(rows)} 家（显示前 {min(args.limit, len(rows))}）")
    if note:
        print(note)
    print(md_table(drop_empty_cols(rows[:args.limit])))
    ti = pro.top_inst(trade_date=d)
    if ti is not None and not ti.empty:
        scale(ti, ["buy", "sell", "net_buy"], 1e8)
        inst = pick(ti, {
            "ts_code": "代码", "exalter": "营业部",
            "buy": "买入(亿)", "sell": "卖出(亿)", "net_buy": "净买(亿)",
        })
        print(f"\n## 营业部明细 · 共 {len(inst)} 行（显示前 {min(args.limit, len(inst))}；买/卖空=单边席位）")
        print(md_table(drop_empty_cols(inst[:args.limit]), limits={"营业部": 44}))


def cmd_dv(args):
    pro, src = get_pro()
    code = norm_code(args.code)
    start, end = date_window(args.days)
    df = pro.daily_basic(ts_code=code, start_date=start, end_date=end).head(args.days)
    rows = pick(df, {
        "trade_date": "日期", "close": "收盘", "turnover_rate": "换手%",
        "pe": "PE(静态)", "pe_ttm": "PE(TTM)", "pb": "PB",
        "total_mv": "总市值(亿)", "circ_mv": "流通市值(亿)",
    })
    for r in rows:
        for k in ("总市值(亿)", "流通市值(亿)"):  # daily_basic 市值单位万元 → 亿
            if k in r:
                r[k] = round(r[k] / 1e4, 2) if isinstance(r[k], (int, float)) else r[k]
    rows = [{k: num(v) for k, v in r.items()} for r in rows]
    rows = drop_empty_cols(rows)
    print(f"## daily_basic 估值交叉 {code} · 近 {len(rows)} 个交易日 · token 来源: {src}")
    print(md_table(rows))
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\nCSV 已落盘（原始值）：{args.csv}")


def cmd_mf(args):
    pro, src = get_pro()
    code = norm_code(args.code)
    start, end = date_window(args.days)
    mf = pro.moneyflow(ts_code=code, start_date=start, end_date=end).head(args.days)
    dl = pro.daily(ts_code=code, start_date=start, end_date=end)[["ts_code", "trade_date", "close", "pct_chg"]]
    merged = mf.merge(dl, on=["ts_code", "trade_date"], how="left")
    # 净流入列上游可能缺失（2026-11-14 实测），本地按「买-卖」补算
    for net, buy, sell in [("net_elg_calc", "buy_elg_amount", "sell_elg_amount"),
                           ("net_lg_calc", "buy_lg_amount", "sell_lg_amount")]:
        if net not in merged.columns:
            merged[net] = merged.get(buy, 0) - merged.get(sell, 0)
    if "net_amount" not in merged.columns:
        elg = merged.get("net_elg_calc", 0)
        lg = merged.get("net_lg_calc", 0)
        merged["net_amount_calc"] = (elg if elg is not None else 0) + (lg if lg is not None else 0)
    scale(merged, ["buy_elg_amount", "sell_elg_amount", "net_elg_calc",
                   "buy_lg_amount", "sell_lg_amount", "net_lg_calc",
                   "net_amount", "net_amount_calc"], 1e4)  # 万元 → 亿
    rows = pick(merged, {
        "trade_date": "日期", "close": "收盘", "pct_chg": "涨跌%",
        "buy_elg_amount": "超大单买(亿)", "sell_elg_amount": "超大单卖(亿)",
        "net_elg_calc": "超大单净(亿)", "net_lg_calc": "大单净(亿)",
        "net_amount": "全部净(亿)", "net_amount_calc": "大单合计净(亿)",
    })
    rows = [{k: num(v) for k, v in r.items()} for r in rows]
    rows = drop_empty_cols(rows)
    print(f"## moneyflow 大单结构 {code} · 近 {len(rows)} 个交易日 · 涨跌幅从 daily 联动（moneyflow 无 pct_change） · token 来源: {src}")
    print(md_table(rows))
    if args.csv:
        merged.to_csv(args.csv, index=False)
        print(f"\nCSV 已落盘（原始值）：{args.csv}")


def cmd_fina(args):
    pro, src = get_pro()
    code = norm_code(args.code)
    # 不传 fields 拉全列（自选 fields 拿不到 end_type；本脚本不请求它，按 end_date 推断报告期）
    df = pro.fina_indicator(ts_code=code).head(args.limit)
    qmap = {"1231": "年报", "0630": "中报", "0331": "一季报", "0930": "三季报"}
    rows = pick(df, {
        "end_date": "报告期", "ann_date": "披露日", "roe": "ROE%", "roe_waa": "ROE(加权)",
        "grossprofit_margin": "毛利率%", "netprofit_margin": "净利率%",
        "netprofit_yoy": "净利同比%", "or_yoy": "营收同比%",
        "debt_assets": "资产负债率%", "eps": "EPS", "bps": "BPS", "ocf_to_or": "现金流/营收",
    })
    for r in rows:
        ed = str(r.get("报告期", ""))
        if len(ed) == 8:
            r["报告期"] = f"{ed}({qmap.get(ed[4:], '?')})"
    rows = [{k: num(v) for k, v in r.items()} for r in rows]
    rows = drop_empty_cols(rows)
    print(f"## fina_indicator 财务复核 {code} · 最近 {len(rows)} 个报告期 · 报告期类型按 end_date 推断 · token 来源: {src}")
    print(md_table(rows))
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\nCSV 已落盘（原始值）：{args.csv}")


def cmd_daily(args):
    pro, src = get_pro()
    code = norm_code(args.code)
    start, end = date_window(args.days)
    df = pro.daily(ts_code=code, start_date=start, end_date=end).head(args.days)
    scale(df, ["amount"], 1e4)  # 万元 → 亿（CSV 落盘用原始 df，见下）
    rows = pick(df, {
        "trade_date": "日期", "open": "开", "high": "高", "low": "低", "close": "收",
        "pct_chg": "涨跌%", "vol": "量(手)", "amount": "额(亿)",
    })
    rows = [{k: num(v) for k, v in r.items()} for r in rows]
    rows = drop_empty_cols(rows)
    print(f"## daily 日线 {code} · 近 {len(rows)} 个交易日 · token 来源: {src}")
    print(md_table(rows))
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\nCSV 已落盘（显示换算值）：{args.csv}")


def main():
    ap = argparse.ArgumentParser(
        prog="tsq.py",
        description="Tushare 个股研究速查（token 三路自动解析，统一 markdown 表输出，已知接口坑内置规避）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke", help="冒烟：交易日历验证 token/环境")
    s.add_argument("--debug", action="store_true")
    s.set_defaults(fn=cmd_smoke, days=0, limit=5, csv=None)

    s = sub.add_parser("lhb", help="龙虎榜：top_list + top_inst（必传交易日，逐日查）")
    s.add_argument("date", help="交易日 YYYYMMDD")
    s.add_argument("--limit", type=int, default=15, help="每表最多显示 N 行（默认 15）")
    s.add_argument("--debug", action="store_true")
    s.set_defaults(fn=cmd_lhb, days=0, csv=None)

    for name, help_, fn, has_days in [
        ("dv", "估值交叉 daily_basic（PE/PB/市值/换手）", cmd_dv, True),
        ("mf", "大单结构 moneyflow（联动 daily 补涨跌幅，净额本地补算）", cmd_mf, True),
        ("fina", "财务复核 fina_indicator（最近报告期）", cmd_fina, False),
        ("daily", "基础日线行情", cmd_daily, True),
    ]:
        s = sub.add_parser(name, help=help_)
        s.add_argument("code", help="股票代码 600519 或 600519.SH")
        if has_days:
            s.add_argument("--days", type=int, default=10, help="最近 N 个交易日（默认 10）")
        s.add_argument("--limit", type=int, default=8, help="最多显示 N 行（默认 8，fina 为报告期数）")
        s.add_argument("--csv", default=None, help="同时落盘 CSV 到指定路径")
        s.add_argument("--debug", action="store_true", help="打印原始异常")
        s.set_defaults(fn=fn, days=10)

    args = ap.parse_args()
    try:
        args.fn(args)
    except SystemExit:
        raise
    except Exception as e:
        msg = str(e)
        if args.debug:
            import traceback
            traceback.print_exc()
        if "权限" in msg or "积分" in msg or "抱歉" in msg:
            _die(f"接口权限/积分不足（该 token 档位可能不开放此接口）：{msg}", EXIT_PERM)
        if "必填参数" in msg or ("字段" in msg and "不存在" in msg):
            _die(f"参数/字段错误（先查 SKILL.md「已知接口坑」节）：{msg}", EXIT_ARGS)
        _die(f"查询失败：{msg if args.debug else '网络或服务异常，--debug 看原始信息'}", EXIT_NET)


if __name__ == "__main__":
    main()
