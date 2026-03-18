"use client";

import { useEffect, useState } from "react";

import { HistoryPanel } from "./components/HistoryPanel";
import { StudyPanel } from "./components/StudyPanel";
import { ThinkingPanel } from "./components/ThinkingPanel";
import styles from "./page.module.css";
import type {
  ConnectionState,
  SavedSettings,
  Screen,
  StudyResponse,
  ThinkingResponse,
  WorkspaceTab,
} from "./types";

const featureCards = [
  {
    title: "学习",
    text: "围绕题目、讲解、解题和整理，把考试前的短期复习链路做清楚。",
  },
  {
    title: "写作与复盘",
    text: "把随笔、反思和复盘记录收束成下一步能继续推进的草稿。",
  },
  {
    title: "时间暗线",
    text: "真实学习时长、冲刺模式和常规模式在后台工作，但不打断主笔记阅读。",
  },
  {
    title: "本地优先",
    text: "Windows-first，本地设置、本地记录、低噪声界面，先把流程跑通。",
  },
];

const workspaceTabs: { id: WorkspaceTab; label: string; description: string }[] = [
  { id: "study", label: "学习", description: "题目、解题、错题复盘、时间提醒和复习安排。" },
  { id: "thinking", label: "写作与复盘", description: "随笔、反思、复盘和下一步行动。" },
];

const minimaxGuideLinks = [
  { label: "Quickstart", href: "https://platform.minimaxi.com/docs/guides/quickstart" },
  { label: "定价页", href: "https://www.minimaxi.com/pricing" },
  { label: "OpenAI 兼容接口", href: "https://platform.minimaxi.com/docs/api-reference/text-openai-api" },
  { label: "API FAQ", href: "https://platform.minimaxi.com/docs/api-reference/basic-information/faq" },
];

const initialStudy: StudyResponse = {
  knowledge_points: ["题干关键信息", "核心目标", "方法选择"],
  difficulty: "待分析",
  explanation_mode: "简明",
  explanation: "输入题目后，这里会生成一页连续可读的学习笔记，而不是分散的小卡片。",
  solution_steps: ["提取已知条件", "明确要求输出什么", "选择方法并分步展开", "检查结果是否回答原问题"],
  formula_notes: ["先写已知与未知", "先拆问题，再计算"],
  novice_explain: "先看题目问什么，再一条条整理已知信息，最后决定怎么做。",
  review_schedule: ["10 分钟后回看一次", "30 分钟后抽问一次", "12 小时后再回顾", "24 小时后强化"],
  time_plan: ["10 分钟理解题目", "15 分钟跟随步骤", "10 分钟做同类型题", "5 分钟回顾易错点"],
  memory_tips: ["把题目拆成已知、未知、方法三栏", "先圈关键词", "先答核心问题再补细节"],
  exam_tricks: ["先写最确定的一步", "先理清量或条件关系", "答案最后回到原问题"],
  diagram_hint: "如果关系复杂，可以先画结构图、流程图或示意图。",
  variant_questions: ["修改一个已知条件后重做", "换一种提问方式后重做", "加入额外约束后再判断"],
  mini_quiz: ["这题的核心目标是什么？", "最关键的已知条件是哪一个？", "哪一步最容易漏掉？"],
  self_questions: ["题目真正要求我求什么？", "哪些信息还没被用到？", "如果条件变了，方法是否还成立？"],
  practice_set: ["小卷题 1：基础同型题", "小卷题 2：条件变化题", "小卷题 3：综合判断题"],
  examples: ["例题 1：基础版同主题题目", "例题 2：增加一步变形的题目", "例题 3：需要解释过程的题目"],
  exam_focus_prediction: ["已知条件提取", "步骤完整性", "结果回到原问题"],
  next_action: "输入题目后，从讲解和步骤开始往下读。",
  confidence_note: "先把问题结构看清楚，通常就已经走完最难的一半了。",
  risk_notice: "AI 可能产生幻觉，请核对关键步骤。",
  score_breakdown: ["步骤 1：识别题目结构 2 分", "步骤 2：列出关键关系 3 分", "步骤 3：推导或计算 3 分", "步骤 4：回答原问题 2 分"],
};

const initialThinking: ThinkingResponse = {
  mode: "essay",
  title: "把想法写成可继续推进的草稿",
  outline: ["清楚陈述原始想法", "展开其中的矛盾或问题", "落到可执行的行动"],
  content: "这里会把一句话扩展成可读的草稿，并给出下一步行动建议。",
  rewrite_options: ["更克制", "更直接", "复盘口吻"],
  key_points: ["观点一句话", "一个小例子", "一句行动建议"],
  tone_tags: ["克制", "清晰", "不鸡汤"],
  export_title: "examnova-writing.txt",
  summary: "一句话总结：把想法转成可行动的结论。",
  confidence_note: "先把这次写清楚，再决定明天补哪一段，你就在往前走。",
  reflection_prompt: "这段内容里，哪一句最值得你明天继续展开？",
  review_bridge: ["压缩成 3 个关键词", "写下明天的 1 个续写入口", "留下一个 15 分钟内能完成的小目标"],
  action_list: ["写下 3 个关键词", "补充 1 个例子", "落成一句行动"],
};

const settingsStorageKey = "examnova.settings";

type LoadedSettings = {
  provider: string | null;
  base_url: string | null;
  model: string | null;
  demo_mode: boolean;
  mathpix_enabled: boolean;
  mathpix_app_id: string | null;
  mathpix_endpoint: string;
  has_api_key: boolean;
  has_mathpix_app_key: boolean;
};

function SignatureLogo() {
  return (
    <svg className={styles.signatureLogo} viewBox="0 0 960 220" aria-label="ExamNova">
      <text x="50%" y="58%" textAnchor="middle" className={styles.signatureStroke}>
        ExamNova
      </text>
      <text x="50%" y="58%" textAnchor="middle" className={styles.signatureFill}>
        ExamNova
      </text>
    </svg>
  );
}

export default function Home() {
  const [screen, setScreen] = useState<Screen>("splash");
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("study");
  const [backendUrl, setBackendUrl] = useState("http://127.0.0.1:8000");
  const [baseUrl, setBaseUrl] = useState("https://api.minimaxi.com/v1");
  const [model, setModel] = useState("MiniMax-M2.5");
  const [apiKey, setApiKey] = useState("");
  const [demoMode, setDemoMode] = useState(true);
  const [mathpixEnabled, setMathpixEnabled] = useState(false);
  const [mathpixAppId, setMathpixAppId] = useState("");
  const [mathpixAppKey, setMathpixAppKey] = useState("");
  const [mathpixEndpoint, setMathpixEndpoint] = useState("https://api.mathpix.com/v3/text");
  const [hasSavedApiKey, setHasSavedApiKey] = useState(false);
  const [hasSavedMathpixAppKey, setHasSavedMathpixAppKey] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: "idle",
    message: "请先填写 API 信息并测试本地后端连接。",
  });
  const [settingsStatus, setSettingsStatus] = useState<string>("尚未检查配置。");

  useEffect(() => {
    let cancelled = false;
    let savedSettings: SavedSettings | null = null;

    try {
      const savedRaw = window.localStorage.getItem(settingsStorageKey);
      if (savedRaw) {
        savedSettings = JSON.parse(savedRaw) as SavedSettings;
        setBackendUrl(savedSettings.backendUrl || "http://127.0.0.1:8000");
        setBaseUrl(savedSettings.baseUrl || "https://api.minimaxi.com/v1");
        setModel(savedSettings.model || "MiniMax-M2.5");
        setDemoMode(savedSettings.demoMode ?? true);
        setMathpixEnabled(savedSettings.mathpixEnabled ?? false);
        setMathpixAppId(savedSettings.mathpixAppId || "");
        setMathpixEndpoint(savedSettings.mathpixEndpoint || "https://api.mathpix.com/v3/text");
      }
    } catch {
      // Ignore malformed local settings and keep defaults.
    }

    const initialBackendUrl = savedSettings?.backendUrl || "http://127.0.0.1:8000";
    void (async () => {
      const candidates = Array.from(
        new Set([initialBackendUrl, "http://127.0.0.1:8000", "http://127.0.0.1:8001"].filter(Boolean)),
      );

      for (const candidate of candidates) {
        try {
          const response = await fetch(`${candidate}/api/settings/load`);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const payload = (await response.json()) as LoadedSettings;
          if (cancelled) {
            return;
          }
          setBackendUrl(candidate);
          setBaseUrl(payload.base_url || "https://api.minimaxi.com/v1");
          setModel(payload.model || "MiniMax-M2.5");
          setDemoMode(payload.demo_mode ?? true);
          setMathpixEnabled(payload.mathpix_enabled ?? false);
          setMathpixAppId(payload.mathpix_app_id || "");
          setMathpixEndpoint(payload.mathpix_endpoint || "https://api.mathpix.com/v3/text");
          setHasSavedApiKey(payload.has_api_key);
          setHasSavedMathpixAppKey(payload.has_mathpix_app_key);
          return;
        } catch {
          // Try the next candidate.
        }
      }
    })();

    const timer = window.setTimeout(() => {
      if (savedSettings?.onboardingComplete) {
        setScreen("home");
        return;
      }
      setScreen("welcome");
    }, 2200);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  function persistSettings(onboardingComplete: boolean) {
    const saved: SavedSettings = {
      backendUrl,
      baseUrl,
      model,
      demoMode,
      mathpixEnabled,
      mathpixAppId,
      mathpixEndpoint,
      onboardingComplete,
    };
    window.localStorage.setItem(settingsStorageKey, JSON.stringify(saved));
  }

  function buildSettingsPayload() {
    return {
      provider: "minimax",
      base_url: baseUrl,
      model,
      api_key: apiKey,
      demo_mode: demoMode,
      reuse_saved_credentials: (!apiKey && hasSavedApiKey) || (!mathpixAppKey && hasSavedMathpixAppKey),
      mathpix_enabled: mathpixEnabled,
      mathpix_app_id: mathpixAppId,
      mathpix_app_key: mathpixAppKey,
      mathpix_endpoint: mathpixEndpoint,
    };
  }

  async function testConnection() {
    setConnectionState({ status: "loading", message: "正在测试后端与模型连接..." });

    try {
      const response = await fetch(`${backendUrl}/api/settings/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(buildSettingsPayload()),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = (await response.json()) as { ok: boolean; message: string };
      persistSettings(false);
      setConnectionState({
        status: payload.ok ? "success" : "error",
        message: payload.message,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setConnectionState({
        status: "error",
        message: `连接失败：${message}`,
      });
    }
  }

  async function checkSettingsStatus() {
    try {
      const response = await fetch(`${backendUrl}/api/settings/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = (await response.json()) as {
        ready: boolean;
        missing: string[];
        provider: string | null;
        model: string | null;
        demo_mode?: boolean;
        has_api_key?: boolean;
      };
      setHasSavedApiKey(Boolean(payload.has_api_key));
      if (payload.ready) {
        const demoNote = payload.demo_mode ? "（演示模式）" : "";
        setSettingsStatus(`配置已就绪${demoNote}：${payload.provider ?? "unknown"} / ${payload.model ?? "unknown"}`);
      } else {
        setSettingsStatus(`缺少：${payload.missing.join("、")}`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setSettingsStatus(`检查失败：${message}`);
    }
  }

  function continueToWorkspace() {
    persistSettings(true);
    setScreen("home");
  }

  function openPreview() {
    persistSettings(false);
    setScreen("home");
  }

  async function saveSettings() {
    persistSettings(true);

    try {
      const response = await fetch(`${backendUrl}/api/settings/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(buildSettingsPayload()),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      setHasSavedApiKey(Boolean(apiKey) || hasSavedApiKey);
      setHasSavedMathpixAppKey(Boolean(mathpixAppKey) || hasSavedMathpixAppKey);
      setConnectionState({
        status: "success",
        message: "设置已保存。敏感凭据保留在后端本地数据目录中，不写入浏览器本地存储。",
      });
    } catch {
      setConnectionState({
        status: "error",
        message: "保存到后端失败，当前仅保留了浏览器中的非敏感设置。",
      });
    }
  }

  const renderMain = () => {
    if (screen === "splash") {
      return (
        <section className={styles.splash}>
          <div className={styles.splashInner}>
            <div className={styles.signatureWrap}>
              <SignatureLogo />
            </div>
            <div className={styles.splashSub}>Study, review, and write with a calm local workflow.</div>
          </div>
        </section>
      );
    }

    if (screen === "welcome") {
      return (
        <section className={styles.shell}>
          <div className={styles.hero}>
            <div className={styles.eyebrow}>ExamNova</div>
            <h1 className={styles.title}>面向中国大学生的桌面复习工作台</h1>
            <p className={styles.lead}>
              它不是泛聊天助手，而是围绕题目、复习和写作整理设计的本地工作台。理解题目、整理笔记、回看重点、继续写下去，都在一条清楚的链路里。
            </p>
            <div className={styles.actions}>
              <button className={styles.primary} onClick={() => setScreen("features")}>
                开始引导
              </button>
              <button className={styles.secondary} onClick={openPreview}>
                进入预览
              </button>
            </div>
          </div>

          <aside className={styles.panel}>
            <h2 className={styles.panelTitle}>第一版要解决的三件事</h2>
            <ol className={styles.list}>
              <li>把复习链路做成清楚的产品结构。</li>
              <li>让 API 配置和本地运行不再吓人。</li>
              <li>用低噪声界面减少拖延和切换成本。</li>
            </ol>
            <div className={styles.footerNote}>这个项目更看重结构化推进，而不是热闹的陪伴感。</div>
          </aside>
        </section>
      );
    }

    if (screen === "features") {
      return (
        <section className={styles.shell}>
          <div className={styles.hero}>
            <div className={styles.eyebrow}>核心能力</div>
            <h1 className={styles.title}>一个 Agent，两条主线，一条真实复习链路</h1>
            <div className={styles.grid}>
              {featureCards.map((feature) => (
                <article key={feature.title} className={styles.card}>
                  <h2 className={styles.cardTitle}>{feature.title}</h2>
                  <p className={styles.cardText}>{feature.text}</p>
                </article>
              ))}
            </div>
            <div className={styles.actions}>
              <button className={styles.primary} onClick={() => setScreen("setup")}>
                继续设置
              </button>
              <button className={styles.secondary} onClick={() => setScreen("welcome")}>
                返回
              </button>
            </div>
          </div>

          <aside className={styles.panel}>
            <h2 className={styles.panelTitle}>产品边界</h2>
            <ul className={styles.list}>
              <li>主线是学习与复盘，不做泛聊天产品。</li>
              <li>给信心，但不用鸡汤和口号。</li>
              <li>优先本地可运行、可解释、可演示。</li>
            </ul>
          </aside>
        </section>
      );
    }

    if (screen === "setup") {
      return (
        <section className={styles.shell}>
          <div className={styles.hero}>
            <div className={styles.eyebrow}>配置</div>
            <h1 className={styles.title}>先连通，再进入工作区</h1>
            <p className={styles.lead}>
              这里会测试真实后端和模型连接。非敏感设置保存在浏览器本地，敏感凭据保存在应用本地数据目录中。
            </p>

            <details className={styles.collapsePanel}>
              <summary>不会购买 MiniMax API？打开新手教程</summary>
              <div className={styles.collapseInner}>
                <div className={styles.guideStack}>
                  <p className={styles.cardText}>最短路线是：注册平台账号，查看价格页，确认是否先试用或充值，创建 API Key，再回到 ExamNova 填写连接信息。</p>

                  <div className={styles.subtlePanel}>
                    <strong className={styles.guideTitle}>在 ExamNova 里这样填</strong>
                    <ul className={styles.list}>
                      <li>`Base URL`：`https://api.minimaxi.com/v1`</li>
                      <li>`Model`：可以先用 `MiniMax-M2.5`</li>
                      <li>`API Key`：填写你刚创建的 Key</li>
                    </ul>
                  </div>

                  <div className={styles.subtlePanel}>
                    <strong className={styles.guideTitle}>官方入口</strong>
                    <ul className={styles.list}>
                      {minimaxGuideLinks.map((item) => (
                        <li key={item.href}>
                          <a className={styles.inlineLink} href={item.href} target="_blank" rel="noreferrer">
                            {item.label}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className={styles.subtlePanel}>
                    <strong className={styles.guideTitle}>给第一次购买的人</strong>
                    <ol className={styles.list}>
                      <li>先看官方价格页，不要只看第三方截图。</li>
                      <li>如果平台有试用额度，先用试用额度跑通。</li>
                      <li>如果你准备长期用，再充值或选适合自己的套餐。</li>
                      <li>创建好 Key 后，先点“测试连接”，通过后再进工作区。</li>
                    </ol>
                  </div>

                  <p className={styles.footerNote}>
                    价格、套餐名和可用模型都可能变化；真正付款前请以官方页面为准。仓库里也提供了纯文本版本教程：`docs/MINIMAX-BEGINNER.txt`。
                  </p>
                </div>
              </div>
            </details>

            <div className={styles.formGrid}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="backend-url">
                  本地后端地址
                </label>
                <input
                  className={styles.input}
                  id="backend-url"
                  value={backendUrl}
                  onChange={(event) => setBackendUrl(event.target.value)}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="base-url">
                  LLM Base URL
                </label>
                <input className={styles.input} id="base-url" value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
                <div className={styles.hint}>中国建议使用 https://api.minimaxi.com/v1，海外可用 https://api.minimax.io/v1</div>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="model">
                  模型名称
                </label>
                <input className={styles.input} id="model" value={model} onChange={(event) => setModel(event.target.value)} />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="api-key">
                  API Key
                </label>
                <input
                  className={styles.input}
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder={hasSavedApiKey ? "留空则沿用后端已保存 Key" : "粘贴你的 API Key"}
                />
                <div className={styles.hint}>浏览器不会记住这个 Key。</div>
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="demo-mode">
                演示模式（不调用外部接口）
              </label>
              <div className={styles.checkboxRow}>
                <input
                  id="demo-mode"
                  type="checkbox"
                  className={styles.checkbox}
                  checked={demoMode}
                  onChange={(event) => setDemoMode(event.target.checked)}
                />
                <span className={styles.hint}>关闭后会进行真实模型请求测试。</span>
              </div>
            </div>

            <div className={styles.panel}>
              <h2 className={styles.panelTitle}>Mathpix OCR（数学识别特化）</h2>
              <div className={styles.field}>
                <div className={styles.checkboxRow}>
                  <input
                    id="mathpix-enabled"
                    type="checkbox"
                    className={styles.checkbox}
                    checked={mathpixEnabled}
                    onChange={(event) => setMathpixEnabled(event.target.checked)}
                  />
                  <label className={styles.label} htmlFor="mathpix-enabled">
                    启用 Mathpix
                  </label>
                </div>
                <div className={styles.hint}>Mathpix 涉及计费，请确认已开通计费并管理好余额。</div>
              </div>

              <div className={styles.formGrid}>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="mathpix-app-id">
                    Mathpix App ID
                  </label>
                  <input
                    className={styles.input}
                    id="mathpix-app-id"
                    value={mathpixAppId}
                    onChange={(event) => setMathpixAppId(event.target.value)}
                    placeholder="app_id"
                    disabled={!mathpixEnabled}
                  />
                </div>

                <div className={styles.field}>
                  <label className={styles.label} htmlFor="mathpix-app-key">
                    Mathpix App Key
                  </label>
                  <input
                    className={styles.input}
                    id="mathpix-app-key"
                    type="password"
                    value={mathpixAppKey}
                    onChange={(event) => setMathpixAppKey(event.target.value)}
                    placeholder={hasSavedMathpixAppKey ? "留空则沿用后端已保存 Key" : "app_key"}
                    disabled={!mathpixEnabled}
                  />
                </div>

                <div className={styles.field}>
                  <label className={styles.label} htmlFor="mathpix-endpoint">
                    Mathpix Endpoint
                  </label>
                  <input
                    className={styles.input}
                    id="mathpix-endpoint"
                    value={mathpixEndpoint}
                    onChange={(event) => setMathpixEndpoint(event.target.value)}
                    disabled={!mathpixEnabled}
                  />
                  <div className={styles.hint}>默认地址：https://api.mathpix.com/v3/text</div>
                </div>
              </div>
            </div>

            <div className={styles.actions}>
              <button className={styles.primary} onClick={testConnection}>
                {connectionState.status === "loading" ? "正在测试..." : "测试连接"}
              </button>
              <button className={styles.secondary} onClick={checkSettingsStatus}>
                检查配置
              </button>
              <button
                className={styles.secondary}
                onClick={() => {
                  void saveSettings();
                  continueToWorkspace();
                }}
              >
                进入工作区
              </button>
            </div>
          </div>

          <aside className={styles.panel}>
            <h2 className={styles.panelTitle}>连接状态</h2>
            <div className={styles.statusBox} data-status={connectionState.status}>
              {connectionState.message}
            </div>
            <div className={styles.statusLine}>{settingsStatus}</div>
            <div className={styles.credentialNote}>
              <strong>凭据说明：</strong>
              <span>{hasSavedApiKey ? "后端本地已保存 API Key。" : "当前尚未检测到已保存的 API Key。"}</span>
            </div>
            {demoMode ? (
              <div className={styles.demoNotice}>
                当前为演示模式：不会调用外部 LLM 接口，适合先确认工作流与页面结构。
              </div>
            ) : null}
            <div className={styles.footerNote}>第一版先保证连接可信、边界清楚，再继续做更深的技能扩展。</div>
          </aside>
        </section>
      );
    }

    return (
      <section className={styles.workspace}>
        <header className={styles.workspaceHeader}>
          <div>
            <div className={styles.eyebrow}>工作区</div>
            <h1 className={styles.workspaceTitle}>ExamNova 工作台</h1>
            <p className={styles.workspaceLead}>一页一题，按康奈尔笔记的阅读顺序往下走，其他工具尽量收起。</p>
          </div>
          <div className={styles.actions}>
            <button className={styles.secondary} onClick={() => setScreen("setup")}>
              打开设置
            </button>
          </div>
        </header>

        <div className={styles.workspaceBody}>
          <nav className={styles.sidebar}>
            {workspaceTabs.map((tab) => (
              <button
                key={tab.id}
                className={styles.navButton}
                data-active={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className={styles.navLabel}>{tab.label}</span>
                <span className={styles.navDescription}>{tab.description}</span>
              </button>
            ))}
          </nav>

          <div className={styles.contentPanel}>
            {activeTab === "study" && <StudyPanel backendUrl={backendUrl} initialData={initialStudy} />}
            {activeTab === "thinking" && <ThinkingPanel backendUrl={backendUrl} initialData={initialThinking} />}

            <details className={styles.historyDock}>
              <summary className={styles.historyDockSummary}>最近记录与导出</summary>
              <div className={styles.historyDockInner}>
                <HistoryPanel backendUrl={backendUrl} compact />
              </div>
            </details>
          </div>
        </div>
      </section>
    );
  };

  return <main className={styles.page}>{renderMain()}</main>;
}
