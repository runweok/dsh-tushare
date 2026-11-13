# dsh-tushare · Tushare 行情研究（含技能）

DeepSeek Harness（DSH）插件：**给所有会话安装 tushare-data 数据研究技能**，并在插件设置里提供 Tushare Token 输入框——填一次 token，所有会话开箱即用，不依赖环境变量和 `~/.tushare/token`。

## 功能

### 1. 完整数据研究技能，装完即用

插件启用后自动把 `tushare-data` 数据研究技能同步到 `~/.dsh/skills/tushare-data/`，**所有会话即刻可用**。技能由 tushare.pro 官方 OpenClaw 技能（v1.1.10）移植适配，完整覆盖：

- **10 类研究意图，中文自然语言直达**：行情/趋势 · 标的识别 · 财务/公司质量 · 估值/基本面 · 资金流/市场行为 · 板块/指数/主题 · 打板/情绪/活跃度 · 公告/新闻/研报/政策 · 宏观/跨市场 · 数据导出
- **229 个 Tushare 接口字段速查**（`references/数据接口.md`）：股票参考数据、债券、两融及转融通、ETF/基金、宏观价格指数、行业经济（TMT）、大模型语料等分类的全字段/参数表
- **口语化触发示例**：
  - 「北向资金最近在买什么」（资金流）
  - 「查一下今天的龙虎榜」（龙虎榜/营业部明细）
  - 「XX 最近走势怎么样」（行情/趋势）
  - 「最近哪个板块最强」（板块/主题）
  - 「帮我看下 XX 的财报质量」（财务/估值）
  - 「导出 XX 日线 CSV / parquet」（研究准备）
- **内置取数脚本**：`scripts/stock_data_demo.py` / `scripts/fund_data_demo.py`，自动走 token 读取链，`pip install tushare pandas` 即可跑通
- **数据纪律内建**：环境前置检查（python/tushare/token）、高权限接口积分提示、数据时点标注要求，全流程写进技能指令

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
