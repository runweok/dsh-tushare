# Changelog

## 2.3.4 (2026-11-14)

- README/SKILL：免费 vs 付费积分档位矩阵（官方口径 2026-11 拉取）与 agent 侧权限门槛速查
- 首发 npm：`dsh-tushare@2.3.4`；仓库根新增 format-1 市场索引 `index.json`

## 2.3.3 (2026-11-14)

- 新增速查 CLI `skill/scripts/tsq.py`：`lhb` / `dv` / `mf` / `fina` / `daily` / `smoke` 六个子命令
  - token 三路自动解析、统一 markdown 紧凑表（中文对齐、单位换算为亿、数据时点标注）
  - 已知接口坑内置规避：top_list 逐日查、moneyflow 涨跌幅联动 daily + 净额本地补算、报告期推断
  - 分档退出码（0 成功 / 2 参数 / 3 权限积分 / 4 网络）

## 2.3.2 (2026-11-14)

- SKILL.md 新增「与 westock-data 的路由分工」声明（选择层 description 硬断言 + 正文分工节）
- SKILL.md 新增「已知接口坑（持续回写）」账本：`top_list` 当前档必传 `trade_date`、`moneyflow` 无 `pct_change` 列、`fina_indicator` 自选 fields 不返回 `end_type`

## 2.3.1 (2026-11-14)

- 首个公开版本
- 技能自动安装：启用即同步 `tushare-data` 到 `~/.dsh/skills/tushare-data/`（SKILL.md + 229 接口速查 + 演示脚本）
- Token 三通道：设置页输入框（`plugins.bundle.config` slot）/ `/tushare-token` 命令 / `tushare_set_token` 工具；0600 落盘、不回显
- 本地设置 API：`/api/plugins/tushare/settings`，同源校验 + body 限长
- Windows 兼容：路径全部 `os.homedir()` 解析
- 发布化：MIT、engines.dsh、exports/files 清单、双语 locale、自绘 icon
