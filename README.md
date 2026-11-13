# dsh-tushare · Tushare 行情研究（含技能）

DeepSeek Harness（DSH）插件：**给所有会话安装 tushare-data 数据研究技能**，并在插件设置里提供 Tushare Token 输入框——填一次 token，所有会话开箱即用。从龙虎榜、北向资金、打板情绪到宏观跨市场，中文自然语言直接出研究结论和数据文件。

## 功能

### 1. 完整数据研究技能，装完即用

插件启用后自动把 `tushare-data` 数据研究技能同步到 `~/.dsh/skills/tushare-data/`，**所有会话即刻可用**。技能由 tushare.pro 官方 OpenClaw 技能（v1.1.10）移植适配，完整保留全部能力。

**10 类研究意图，中文自然语言直达**：行情/趋势 · 标的识别 · 财务/公司质量 · 估值/基本面 · 资金流/市场行为 · 板块/指数/主题 · 打板/情绪/活跃度 · 公告/新闻/研报/政策 · 宏观/跨市场 · 数据导出

**特色数据一网打尽**：

- **龙虎榜**：`top_list` 个股上榜 + `top_inst` 营业部买卖明细
- **北向/沪深港通**：`moneyflow_hsgt` 资金流向、`hsgt_top10` 活跃股排行，另有主力资金流 `moneyflow` 与板块资金流（东财口径）
- **打板情绪面**：涨停/跌停列表 `limit_list_d`、连板梯队 `limit_step`、开盘啦 `kpl_list`、东财/同花顺热榜 `dc_hot`/`ths_hot`
- **板块三口径**：申万行业、同花顺概念、东财板块任选，成分股/资金流/涨停梯队联动分析
- **财报事件链**：业绩预告 `forecast`、业绩快报 `express`、披露时间表 `disclosure_date`、互动易/上证 e 互动问答
- **两融及转融通**：37 个接口全覆盖；**债券专题** 82 个接口
- **宏观全家桶 + 跨市场**：CPI/PPI/PMI/GDP/M2/社融、Shibor/LPR、美债收益率，港股/美股/全球指数
- **分钟线与实时**：`stk_mins` 历史分钟，`rt_k`/`rt_min` 实时口径（按权限）

**9 大研究工作流模板（不止查数，直接出结论）**：

| 工作流 | 口语示例 |
|---|---|
| 单标的行情分析 | 「看下 XX 最近怎么样」 |
| 多标的横向对比 | 「比一下茅台、五粮液、泸州老窖近一年涨幅和估值」 |
| 财务质量快照 | 「比亚迪最近 8 个季度营收利润趋势」 |
| 估值分析/筛选 | 「筛一批高 ROE 低负债的公司」 |
| 资金流追踪 | 「北向最近在买什么」 |
| 板块/题材轮动 | 「最近哪个板块最强，强在哪些票」 |
| 公告/事件梳理 | 「帮我梳理下寒武纪最近的重要公告」 |
| 数据导出与研究准备 | 「沪深300成分股近两年日线导成 CSV」 |
| 综合研究简报 | 「快速研究一下 XX，给个全景判断」 |

**工程化数据纪律**（不是只会调接口）：

- 模糊口语自动落到合理口径：「最近」→ 近 20 交易日、「财报」→ 近 8 季度+年度、「强不强」→ 走势+相对强弱+活跃度
- 长区间自动分段拉取、限流重试、断点续跑、基础表缓存复用
- 输出契约固定：一句话结论 + 数据口径 + 关键表格 + 风险点 + 文件路径
- 空结果会区分非交易日/未上市/无权限，不会把空表说成「接口坏了」
- 导出 CSV/Parquet 附元信息（接口名、参数、拉取时间、行数、失败分段），可直接进回测
- **229 个接口字段速查**（`references/数据接口.md`）：股票参考、债券、两融转融通、ETF/基金、宏观、行业经济、大模型语料全分类
- **内置取数脚本**：`scripts/stock_data_demo.py` / `scripts/fund_data_demo.py`，`pip install tushare pandas` 即可跑通

### 2. Token 管理（三条通道）
   - **设置页输入框（推荐）**：**设置 → 插件 → Tushare** 页签，粘贴 token 点保存（插件自带该页签）
   - 任意会话输入命令：**`/tushare-token <你的token>`**（`/tushare-token` 查看来源状态，`/tushare-token clear` 清除）
   - 或直接对 AI 说「**把 tushare token 设为 xxx**」（调用 `tushare_set_token` 工具）
   - token 自动写入技能目录（0600 权限），技能脚本开箱即用；清除则回退 `~/.tushare/token` 或环境变量 `TUSHARE_TOKEN`

## 界面预览

插件详情页内置 Tushare Token 设置面板（状态指示 / 保存 / 清除）：

![插件详情页的 Tushare Token 设置面板](https://raw.githubusercontent.com/runweok/dsh-tushare/main/docs/screenshot-token-settings.png)

## 安装（三种方式任选）

1. **npm 包（推荐）**：对本机 DSH 里的 AI 说：**用 plugin_manager 的 install_bundle 安装 dsh-tushare**（target 给 `dsh-tushare@<版本号>`）
2. **Git 钉扎**：install_bundle target 给 `github:runweok/dsh-tushare#<commit>`（锁定具体 commit，适合复现）
3. **市场索引订阅**：仓库根 `index.json`（format-1）发布后，可经 raw.githubusercontent 索引源订阅，Discover 搜索可见

装好后：任意会话输入 `/tushare-token <token>` 设置 token；验证：开个会话说「北向资金最近在买什么」或「查一下 XX 的龙虎榜」。

## Token 读取链

`TUSHARE_TOKEN` 环境变量 → 技能目录 token 文件（命令/工具写入）→ `~/.tushare/token` → `ts.get_token()`。四条链路任一可用即可。

## 设计说明

- 技能本体由 tushare.pro 官方 OpenClaw 技能（v1.1.10）移植适配，`references/数据接口.md` 为 229 个接口的字段/参数速查表
- 零 Harness 包依赖（服务全部通过运行时 ctx 注入获取）；token 输入走三条通道（设置页输入框 / `/tushare-token` 命令 / `tushare_set_token` 工具），不走 schemastery Config 表单
- token 只存在本机技能目录（0600），不回显、不进任何日志

## License

[MIT](LICENSE)
