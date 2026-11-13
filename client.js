/**
 * dsh-tushare client half：在「设置 → 插件」注册 Tushare 页签，提供
 * token 输入框（写入走 Host 的 /api/plugins/tushare/settings 本地路由）。
 */
window.__ModuleLoader__.load({
	id: "dsh-tushare",
	factory(require) {
		const React = require("react");
		const h = React.createElement;

		const css = `
.dsh-ts-panel{max-width:560px;display:flex;flex-direction:column;gap:12px;color:var(--dsw-alias-label-primary);font-size:13px}
.dsh-ts-title{margin:0;font-size:15px;font-weight:600}
.dsh-ts-hint{margin:0;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.dsh-ts-status{display:flex;align-items:center;gap:6px;color:var(--dsw-alias-label-secondary)}
.dsh-ts-dot{width:8px;height:8px;border-radius:50%;flex:none}
.dsh-ts-row{display:flex;gap:8px}
.dsh-ts-input{flex:1;min-width:0;padding:6px 10px;font:inherit;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-fill-neutral-l1);border:.5px solid var(--dsw-alias-border-l2);border-radius:8px;outline:none}
.dsh-ts-input:focus{border-color:var(--dsw-alias-state-business-primary);outline:var(--dsw-focus-ring-width) solid var(--dsw-focus-ring-color,var(--dsw-alias-state-business-primary));outline-offset:1px}
.dsh-ts-btn{padding:6px 14px;font:inherit;font-size:13px;cursor:pointer;border-radius:8px;border:.5px solid var(--dsw-alias-border-l2);background:var(--dsw-alias-fill-neutral-l1);color:var(--dsw-alias-label-primary)}
.dsh-ts-btn:hover{background:var(--dsw-alias-fill-neutral-l2)}
.dsh-ts-btn:disabled{opacity:.5;cursor:default}
.dsh-ts-primary{background:var(--dsw-alias-state-business-primary);border-color:transparent;color:#fff}
.dsh-ts-primary:hover{background:var(--dsw-alias-state-business-primary);opacity:.9}
.dsh-ts-msg{margin:0;font-size:12px;min-height:16px}
.dsh-ts-msg[data-ok=true]{color:var(--dsw-alias-state-success)}
.dsh-ts-msg[data-ok=false]{color:var(--dsw-alias-state-danger)}
`;

		function styleId() {
			return "dsh-tushare-settings";
		}

		function ensureStyle() {
			if (typeof document === "undefined") return;
			if (document.querySelector(`style[data-plugin-css="${styleId()}"]`) !== null) return;
			const tag = document.createElement("style");
			tag.dataset.plugin = "dsh-tushare";
			tag.dataset.pluginCss = styleId();
			tag.textContent = css;
			document.head.appendChild(tag);
		}

		const API = "/api/plugins/tushare/settings";

		function TushareTokenPanel() {
			const [status, setStatus] = React.useState("…");
			const [configured, setConfigured] = React.useState(null);
			const [tail, setTail] = React.useState("");
			const [value, setValue] = React.useState("");
			const [busy, setBusy] = React.useState(false);
			const [message, setMessage] = React.useState(null);

			React.useEffect(() => {
				let alive = true;
				fetch(API).then((r) => r.json()).then((data) => {
					if (!alive) return;
					setStatus(data.status ?? "未知");
					setConfigured(Boolean(data.configured));
					setTail(typeof data.tail === "string" ? data.tail : "");
				}).catch(() => {
					if (alive) setStatus("状态查询失败（Host 路由未就绪）");
				});
				return () => { alive = false; };
			}, []);

			async function post(payload) {
				setBusy(true);
				setMessage(null);
				try {
					const r = await fetch(API, {
						method: "POST",
						headers: { "content-type": "application/json" },
						body: JSON.stringify(payload)
					});
					const data = await r.json();
					setMessage({ ok: data.ok === true, text: data.ok ? (payload.clear ? "已清除。" : `已保存（长度 ${data.length}）。`) : (data.message ?? "保存失败。") });
					if (data.status !== undefined) setStatus(data.status);
					if (typeof data.configured === "boolean") setConfigured(data.configured);
					if (typeof data.tail === "string") setTail(data.tail);
					if (data.ok && payload.clear !== true) setConfigured(true);
					if (data.ok && payload.clear === true) setConfigured(false);
					if (data.ok && payload.clear !== true) setValue("");
				} catch {
					setMessage({ ok: false, text: "请求失败。" });
				} finally {
					setBusy(false);
				}
			}

			ensureStyle();
			return h("div", { className: "dsh-ts-panel" },
				h("h3", { className: "dsh-ts-title" }, "Tushare Token"),
				h("p", { className: "dsh-ts-hint" },
					"填写 tushare.pro 的 token 后保存，所有会话的 Tushare 数据研究技能即刻可用；留空清除则回退 ~/.tushare/token 或环境变量。也可在会话里用 /tushare-token 命令。"),
				h("div", { className: "dsh-ts-status" },
					h("span", { className: "dsh-ts-dot", style: { background: configured === null ? "var(--dsw-alias-label-tertiary)" : configured ? "var(--dsw-alias-state-success)" : "var(--dsw-alias-state-danger)" } }),
					h("span", null, status)),
				h("div", { className: "dsh-ts-row" },
					h("input", {
						className: "dsh-ts-input",
						type: "password",
						placeholder: configured && tail ? `已保存（…${tail}），粘贴新 token 覆盖` : "粘贴 Tushare token",
						value,
						spellCheck: false,
						autoComplete: "off",
						onChange: (e) => setValue(e.target.value),
						onKeyDown: (e) => {
							if (e.key === "Enter" && value.trim() && !busy) post({ token: value.trim() });
						}
					}),
					h("button", {
						className: "dsh-ts-btn dsh-ts-primary",
						type: "button",
						disabled: busy || !value.trim(),
						onClick: () => post({ token: value.trim() })
					}, "保存"),
					h("button", {
						className: "dsh-ts-btn",
						type: "button",
						disabled: busy || configured === false,
						onClick: () => post({ clear: true })
					}, "清除")),
				message === null ? h("p", { className: "dsh-ts-msg" }) : h("p", { className: "dsh-ts-msg", "data-ok": message.ok ? "true" : "false" }, message.text)
			);
		}

		return {
			inject: ["slots"],
			apply(ctx) {
				// 插件详情页（bundle 页面）内的配置区：key = bundle 包名
				ctx.slots.inject("plugins.bundle.config", () => ctx.slots.register({
					name: "plugins.bundle.config",
					key: "dsh-tushare"
				}, TushareTokenPanel));
			}
		};
	}
});
