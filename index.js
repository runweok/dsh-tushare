/**
 * dsh-tushare：把 Tushare 数据研究技能带给每一个 DSH 会话。
 *
 * 职责：
 * 1. 安装时把自带的 `tushare-data` 技能同步到 `~/.dsh/skills/tushare-data/`
 *    （技能目录会被 DSH 自动收录，所有会话可用）。
 * 2. 提供两条 token 输入通道（桌面插件详情页不渲染 Config 表单，故不走
 *    schemastery Config）：
 *    - 会话命令 `/tushare-token <token>`（查看状态 / 设置 / 清除）
 *    - agent 工具 `tushare_set_token`（对话式："帮我把 token 设为 xxx"）
 *    两者都物化到 `~/.dsh/skills/tushare-data/token`（0600），技能脚本开箱即用。
 *
 * token 读取链（脚本侧）：TUSHARE_TOKEN 环境变量 → 技能目录 token 文件
 *   → ~/.tushare/token → ts.get_token()。
 *
 * 零 Harness 包导入。
 * @module dsh-tushare
 */

import {
	chmodSync,
	constants as fsConstants,
	cpSync,
	existsSync,
	mkdirSync,
	readFileSync,
	unlinkSync,
	writeFileSync
} from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** 插件名（Loader 注册用）。 */
const name = "tushare";
/** 本插件需要注入的服务：工具注册 + 命令注册 + 本地 Web 路由。 */
const inject = ["tools", "commands", "webServer"];

/** 技能落地目录。 */
const SKILL_DIR = join(homedir(), ".dsh", "skills", "tushare-data");
/** 插件包内自带的技能源目录。 */
const SKILL_SRC = join(dirname(fileURLToPath(import.meta.url)), "skill");
/** 物化出的 token 文件。 */
const TOKEN_FILE = join(SKILL_DIR, "token");
/** 兼容回退：tushare CLI 默认的 token 文件位置。 */
const LEGACY_TOKEN_FILE = join(homedir(), ".tushare", "token");

/** 插件设置里的静态 token（来自 cordis 行 config，可选；优先级最高）。 */
let staticToken = "";

/** 有效的 token：设置值 → 技能目录文件 → ~/.tushare/token。 */
function effectiveToken() {
	if (staticToken) return staticToken;
	try {
		const fileToken = readFileSync(TOKEN_FILE, "utf8").trim();
		if (fileToken) return fileToken;
	} catch {
		// 文件不存在
	}
	try {
		const fileToken = readFileSync(LEGACY_TOKEN_FILE, "utf8").trim();
		if (fileToken) return fileToken;
	} catch {
		// 文件不存在
	}
	return "";
}

/** 把包内 skill/ 同步到技能目录（幂等，增量覆盖）。 */
function syncSkill() {
	if (!existsSync(SKILL_SRC)) return;
	mkdirSync(SKILL_DIR, { recursive: true });
	cpSync(SKILL_SRC, SKILL_DIR, { recursive: true, force: true });
}

/** 写入/清除技能目录 token 文件（0600）。 */
function writeTokenFile(token) {
	if (token) {
		mkdirSync(SKILL_DIR, { recursive: true });
		writeFileSync(TOKEN_FILE, token + "\n", { mode: fsConstants.S_IRUSR | fsConstants.S_IWUSR });
		chmodSync(TOKEN_FILE, 0o600);
	} else if (existsSync(TOKEN_FILE)) {
		unlinkSync(TOKEN_FILE);
	}
}

/** token 来源状态描述（不回显 token 本体）。 */
function tokenStatus() {
	if (staticToken) return "来源：插件设置（静态配置）";
	if (existsSync(TOKEN_FILE)) return "来源：技能目录 token 文件";
	try {
		if (readFileSync(LEGACY_TOKEN_FILE, "utf8").trim()) return "来源：~/.tushare/token";
	} catch {
		// 文件不存在
	}
	if (process.env.TUSHARE_TOKEN?.trim()) return "来源：环境变量 TUSHARE_TOKEN";
	return "未配置——查行情会失败，请用 /tushare-token <token> 设置";
}

/** 纯展示用待执行卡片。 */
function present(title, kind, rawInput) {
	return {
		card: "generic",
		title,
		kind,
		...(rawInput === undefined ? {} : { rawInput })
	};
}

/** 注册 token 设置命令（/tushare-token）与会话工具（tushare_set_token）。 */
function registerCommandAndTool(ctx) {
	ctx.commands.register({
		definitionId: "dsh-tushare/tushare-token",
		name: "tushare-token",
		description: "设置 Tushare Token：/tushare-token <token>；不带参数或 status 查看来源；clear 清除插件管理的 token",
		input: { hint: "[<token>|status|clear]" },
		handler(invocation) {
			const raw = (invocation.rawInput ?? "").trim();
			if (!raw || raw === "status") {
				return { kind: "success", text: `Tushare token ${tokenStatus()}。设置：/tushare-token <token>；清除插件管理的 token：/tushare-token clear。` };
			}
			if (raw === "clear") {
				writeTokenFile("");
				return { kind: "success", text: "已清除技能目录 token 文件（将回退 ~/.tushare/token 或环境变量）。" };
			}
			if (raw.length < 20) {
				return { kind: "error", text: `token 长度 ${raw.length} 似乎过短（一般 40+ 字符），未写入。请确认后重试。` };
			}
			writeTokenFile(raw);
			return { kind: "success", text: `已写入（长度 ${raw.length}，0600 权限）。技能查询现在会使用新 token。` };
		}
	});
	ctx.tools.register({
		name: "tushare_set_token",
		description: "设置 Tushare token（写入 ~/.dsh/skills/tushare-data/token，0600）。用户说「把 tushare token 设为 xxx」时调用；action=clear 清除。设置后无需重启，查询立即生效。",
		parameters: {
			action: {
				type: "string",
				enum: ["set", "clear"],
				description: "set=写入 token（需给 token 参数）；clear=删除插件管理的 token 文件",
				required: true
			},
			token: { type: "string", description: "Tushare token 本体（action=set 时必填）；不要在对话中复述" }
		},
		output: {
			schema: {
				oneOf: [
					{
						type: "object",
						additionalProperties: false,
						properties: {
							action: { type: "string", enum: ["set", "clear"] },
							ok: { type: "boolean", const: true },
							path: { type: "string", description: "token 文件路径" },
							length: { type: "integer", description: "token 长度（不回显本体）" }
						},
						required: ["action", "ok", "path"]
					},
					{
						type: "object",
						additionalProperties: false,
						properties: {
							action: { type: "string", enum: ["set", "clear"] },
							ok: { type: "boolean", const: false },
							message: { type: "string" }
						},
						required: ["action", "ok", "message"]
					}
				]
			},
			render(_args, value) {
				return [{ type: "text", text: JSON.stringify(value) }];
			}
		},
		execute(args) {
			const action = args?.action;
			if (action === "clear") {
				writeTokenFile("");
				return { action: "clear", ok: true, path: TOKEN_FILE };
			}
			const token = typeof args?.token === "string" ? args.token.trim() : "";
			if (!token) {
				return { action: "set", ok: false, message: "缺少 token 参数。" };
			}
			if (token.length < 20) {
				return { action: "set", ok: false, message: `token 长度 ${token.length} 似乎过短（一般 40+ 字符），未写入。` };
			}
			writeTokenFile(token);
			return { action: "set", ok: true, path: TOKEN_FILE, length: token.length };
		},
		presentCall: (callArgs) => present(
			callArgs?.action === "clear" ? "清除 Tushare token" : "设置 Tushare token",
			"other",
			callArgs?.action === "clear" ? undefined : `${(callArgs?.token ?? "").length} 字符`
		)
	});
}

/** 读请求 JSON body（限长防滥用）。 */
function readBody(req) {
	return new Promise((resolve, reject) => {
		let size = 0;
		const chunks = [];
		req.on("data", (chunk) => {
			size += chunk.length;
			if (size > 100_000) {
				reject(new Error("body too large"));
				req.destroy();
				return;
			}
			chunks.push(chunk);
		});
		req.on("end", () => {
			try {
				resolve(chunks.length === 0 ? {} : JSON.parse(Buffer.concat(chunks).toString("utf8")));
			} catch {
				resolve({});
			}
		});
		req.on("error", reject);
	});
}

/** 同源校验：无 Origin（同源 GET/本机 curl）或 Origin 与 Host 同源才放行。 */
function sameOrigin(req) {
	const origin = req.headers.origin;
	if (origin === undefined) return true;
	try {
		return new URL(origin).host === req.headers.host;
	} catch {
		return false;
	}
}

/** 注册本地设置 API：GET 状态 / POST {token} 写入 / POST {clear:true} 清除。 */
function registerSettingsApi(ctx) {
	ctx.effect(() => {
		try {
			return ctx.webServer.register({
				kind: "exact",
				path: "/api/plugins/tushare/settings",
				handler: async (req, res) => {
					const send = (status, value) => {
						res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
						res.end(JSON.stringify(value));
					};
					if (!sameOrigin(req)) return send(403, { ok: false, message: "cross-origin refused" });
					try {
						if (req.method === "GET") {
							const active = effectiveToken();
							return send(200, {
								ok: true,
								status: tokenStatus(),
								configured: active !== "",
								tail: active ? active.slice(-4) : undefined
							});
						}
						if (req.method === "POST") {
							const body = await readBody(req);
							if (body.clear === true) {
								writeTokenFile("");
								return send(200, { ok: true, cleared: true, status: tokenStatus() });
							}
							const token = typeof body.token === "string" ? body.token.trim() : "";
							if (!token) return send(400, { ok: false, message: "缺少 token 字段。" });
							if (token.length < 20) return send(400, { ok: false, message: `token 长度 ${token.length} 过短（一般 40+ 字符）。` });
							writeTokenFile(token);
							return send(200, { ok: true, length: token.length, tail: token.slice(-4), status: tokenStatus() });
						}
						send(405, { ok: false, message: "method not allowed" });
					} catch (error) {
						send(500, { ok: false, message: "internal error" });
					}
				}
			});
		} catch (error) {
			// 旧 fiber 遗留的重复路由：复用存量路由（同逻辑），避免插件激活失败。
			if (error instanceof Error && error.message.includes("duplicate")) return () => {};
			throw error;
		}
	}, "dsh-tushare: token route");
}

/** 插件入口：同步技能 + 注册命令与工具 + 应用静态 token。设置变更会重启插件并再次执行。 */
function apply(ctx, config) {
	staticToken = typeof config?.token === "string" ? config.token.trim() : "";
	syncSkill();
	registerCommandAndTool(ctx);
	registerSettingsApi(ctx);
}

export { apply, inject, name };
