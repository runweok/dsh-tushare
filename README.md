# dsh-tushare · Tushare 行情研究（含技能）

DeepSeek Harness（DSH）插件：**给所有会话安装 tushare-data 数据研究技能**，并在插件设置里提供 Tushare Token 输入框——填一次 token，所有会话开箱即用，不依赖环境变量和 `~/.tushare/token`。

## 功能

1. **技能自动安装**：插件启用后，自动把 `tushare-data` 数据研究技能同步到 `~/.dsh/skills/tushare-data/`，所有会话可用。技能覆盖：龙虎榜、个股资金流、日线行情、每日指标（量比/换手率/估值）、交易日历等 Tushare Pro 数据，中文自然语言直查（如「北向资金最近在买什么」「XX 最近走势」「导出 XX 日线 CSV」），内置 10 类研究意图分类（行情/财务/估值/资金流/板块/公告/宏观/导出等）。
2. **Token 输入（三条通道）**：
   - **设置页输入框（推荐）**：**设置 → 插件 → Tushare** 页签，粘贴 token 点保存（插件自带该页签）
   - 任意会话输入命令：**`/tushare-token <你的token>`**（`/tushare-token` 查看来源状态，`/tushare-token clear` 清除）
   - 或直接对 AI 说「**把 tushare token 设为 xxx**」（调用 `tushare_set_token` 工具）
   - token 自动写入技能目录（0600 权限），技能脚本开箱即用；清除则回退 `~/.tushare/token` 或环境变量 `TUSHARE_TOKEN`

## 安装（三种方式任选）

1. **npm 包（推荐）**：对本机 DSH 里的 AI 说：**用 plugin_manager 的 install_bundle 安装 dsh-tushare**（target 给 `dsh-tushare@<版本号>`）
2. **Git 钉扎**：install_bundle target 给 `github:runweok/dsh-tushare#<commit>`（锁定具体 commit，适合复现）
3. **市场索引订阅**：仓库根 `index.json`（format-1）发布后，可经 raw.githubusercontent 索引源订阅，Discover 搜索可见

装好后：任意会话输入 `/tushare-token <token>` 设置 token；验证：开个会话说「北向资金最近在买什么」或「查一下 XX 的龙虎榜」。

## Token 读取链

`TUSHARE_TOKEN` 环境变量 → 技能目录 token 文件（命令/工具写入）→ `~/.tushare/token` → `ts.get_token()`。四条链路任一可用即可。

## 设计说明

- 技能本体由 tushare.pro 官方 OpenClaw 技能（v1.1.10）移植适配，`references/数据接口.md` 为全接口字段速查
- 零 Harness 包依赖（服务全部通过运行时 ctx 注入获取）；token 输入走三条通道（设置页输入框 / `/tushare-token` 命令 / `tushare_set_token` 工具），不走 schemastery Config 表单
- token 只存在本机技能目录（0600），不回显、不进任何日志

## License

[MIT](LICENSE)
