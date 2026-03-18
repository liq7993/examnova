"use client";

import NextImage from "next/image";
import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import katex from "katex";

import styles from "../page.module.css";
import type { StudyResponse, StudyReviewMode, StudySessionState } from "../types";

type Props = {
  backendUrl: string;
  initialData: StudyResponse;
};

type WrongbookItem = {
  timestamp: string;
  question_text: string;
  summary: string;
  course: string | null;
  difficulty: string | null;
  knowledge_points: string[];
};

type NoteEntry = {
  id: string;
  questionText: string;
  course: string;
  result: StudyResponse;
  sessionState: StudySessionState | null;
  formulaDraft: string;
  diagramNotes: string;
  drawingUrl: string | null;
};

type StudyThread = {
  id: string;
  title: string;
  titleLocked: boolean;
  course: string;
  inputText: string;
  explanationMode: string;
  reviewMode: StudyReviewMode;
  result: StudyResponse;
  noteEntries: NoteEntry[];
  activeEditorEntryId: string;
  formulaDraft: string;
  diagramNotes: string;
  drawingUrl: string | null;
  sessionState: StudySessionState | null;
  status: string;
  createdAt: string;
  updatedAt: string;
};

const THREADS_STORAGE_KEY = "examnova-study-threads-v1";

function createEmptyStudyResponse(): StudyResponse {
  return {
    knowledge_points: [],
    difficulty: "待分析",
    explanation_mode: "concise",
    explanation: "",
    solution_steps: [],
    formula_notes: [],
    novice_explain: "",
    review_schedule: [],
    time_plan: [],
    memory_tips: [],
    exam_tricks: [],
    diagram_hint: "",
    variant_questions: [],
    mini_quiz: [],
    self_questions: [],
    practice_set: [],
    examples: [],
    exam_focus_prediction: [],
    next_action: "",
    confidence_note: "",
    risk_notice: "",
    score_breakdown: [],
  };
}

function createThreadId() {
  return `thread-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function shortenThreadTitle(text: string, limit = 18) {
  const trimmed = text.trim();
  if (!trimmed) {
    return "新线程";
  }
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}…` : trimmed;
}

function formatThreadTime(iso: string) {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "刚刚";
  }
}

function isThreadEmpty(thread: StudyThread) {
  return (
    thread.noteEntries.length === 0 &&
    !thread.inputText.trim() &&
    !thread.result.explanation.trim() &&
    thread.result.knowledge_points.length === 0
  );
}

function buildThreadTitle(questionText: string, course: string, noteEntries: NoteEntry[]) {
  const latestEntry = noteEntries[noteEntries.length - 1];
  if (latestEntry?.questionText.trim()) {
    return shortenThreadTitle(latestEntry.questionText);
  }
  if (questionText.trim()) {
    return shortenThreadTitle(questionText);
  }
  if (course.trim()) {
    return `${course.trim()} 新线程`;
  }
  return "新线程";
}

function createEmptyThread(seedCourse = "电路原理"): StudyThread {
  const now = new Date().toISOString();
  const result = createEmptyStudyResponse();
  return {
    id: createThreadId(),
    title: "新线程",
    titleLocked: false,
    course: seedCourse,
    inputText: "",
    explanationMode: "concise",
    reviewMode: "auto",
    result,
    noteEntries: [],
    activeEditorEntryId: "draft",
    formulaDraft: buildFormulaDraft(result),
    diagramNotes: buildDiagramNotes(result),
    drawingUrl: null,
    sessionState: null,
    status: "等待分析。",
    createdAt: now,
    updatedAt: now,
  };
}

function createImportedThread(entries: NoteEntry[]): StudyThread {
  const latest = entries[entries.length - 1];
  const now = new Date().toISOString();
  return {
    id: createThreadId(),
    title: latest ? shortenThreadTitle(latest.questionText) : "最近归档",
    titleLocked: false,
    course: latest?.course || "课程归档",
    inputText: latest?.questionText || "",
    explanationMode: latest?.result.explanation_mode || "concise",
    reviewMode: "auto",
    result: latest?.result || createEmptyStudyResponse(),
    noteEntries: entries,
    activeEditorEntryId: latest?.id || "draft",
    formulaDraft: latest ? latest.formulaDraft : "",
    diagramNotes: latest ? latest.diagramNotes : "按需要补充图解说明。",
    drawingUrl: latest?.drawingUrl || null,
    sessionState: latest?.sessionState || null,
    status: entries.length ? "已导入最近笔记。" : "等待分析。",
    createdAt: now,
    updatedAt: now,
  };
}

function groupThreadsByCourse(threads: StudyThread[]) {
  const groups = new Map<string, StudyThread[]>();
  threads.forEach((thread) => {
    const key = thread.course.trim() || "未分类";
    const bucket = groups.get(key) || [];
    bucket.push(thread);
    groups.set(key, bucket);
  });
  return Array.from(groups.entries()).map(([courseName, items]) => ({
    courseName,
    items,
  }));
}

function buildFormulaDraft(result: StudyResponse) {
  return result.formula_notes.join("\n");
}

function buildDiagramNotes(result: StudyResponse) {
  return result.diagram_hint || "按需要补充图解说明。";
}

function looksLikeBrokenArchiveText(text: string) {
  const trimmed = text.trim();
  if (!trimmed) {
    return true;
  }
  const questionMarkCount = (trimmed.match(/\?/g) || []).length;
  return trimmed.includes("�") || questionMarkCount >= Math.max(3, Math.floor(trimmed.length / 4));
}

function buildArchiveLabel(entry: NoteEntry, index: number) {
  const source = entry.questionText.trim() || entry.result.knowledge_points[0] || entry.course;
  const shortText = source.length > 18 ? `${source.slice(0, 18)}…` : source;
  return `${index + 1}. ${shortText}`;
}

function escapeHtml(text: string) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderMathText(text: string) {
  const normalized = text
    .replaceAll("\\(", "$")
    .replaceAll("\\)", "$")
    .replaceAll("\\[", "$$")
    .replaceAll("\\]", "$$");
  const pattern = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;
  let lastIndex = 0;
  let html = "";
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(normalized)) !== null) {
    const plain = normalized.slice(lastIndex, match.index);
    html += escapeHtml(plain).replaceAll("\n", "<br />");
    const formula = match[1] ?? match[2] ?? "";
    const displayMode = Boolean(match[1]);
    html += katex.renderToString(formula, {
      throwOnError: false,
      displayMode,
      output: "html",
    });
    lastIndex = pattern.lastIndex;
  }

  html += escapeHtml(normalized.slice(lastIndex)).replaceAll("\n", "<br />");
  return html;
}

export function StudyPanel({ backendUrl, initialData: _initialData }: Props) {
  void _initialData;
  const emptyResult = createEmptyStudyResponse();
  const [inputText, setInputText] = useState("");
  const [course, setCourse] = useState("电路原理");
  const [explanationMode, setExplanationMode] = useState("concise");
  const [reviewMode, setReviewMode] = useState<StudyReviewMode>("auto");
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [ocrStatus, setOcrStatus] = useState("等待 OCR 图片。");
  const [result, setResult] = useState<StudyResponse>(emptyResult);
  const [status, setStatus] = useState("等待分析。");
  const [wrongbookItems, setWrongbookItems] = useState<WrongbookItem[]>([]);
  const [wrongbookStatus, setWrongbookStatus] = useState("未加载错题本。");
  const [formulaDraft, setFormulaDraft] = useState(buildFormulaDraft(emptyResult));
  const [diagramNotes, setDiagramNotes] = useState(buildDiagramNotes(emptyResult));
  const [drawingStatus, setDrawingStatus] = useState("输入需要绘制的几何关系、图像草图或推导示意。");
  const [drawingColor, setDrawingColor] = useState("#2f2b26");
  const [drawingWidth, setDrawingWidth] = useState(2);
  const [drawingUrl, setDrawingUrl] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<StudySessionState | null>(null);
  const [noteEntries, setNoteEntries] = useState<NoteEntry[]>([]);
  const [activeEditorEntryId, setActiveEditorEntryId] = useState<string>("draft");
  const [threads, setThreads] = useState<StudyThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState("");
  const [showRecallPrompt, setShowRecallPrompt] = useState(false);
  const [recallDismissed, setRecallDismissed] = useState(false);
  const threadsReadyRef = useRef(false);
  const hydratingThreadRef = useRef(false);
  const importedHistoryRef = useRef(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const questionRef = useRef<HTMLElement | null>(null);
  const explanationRef = useRef<HTMLElement | null>(null);
  const solutionRef = useRef<HTMLElement | null>(null);
  const shortcutRef = useRef<HTMLElement | null>(null);
  const summaryRef = useRef<HTMLElement | null>(null);
  const difficultyText = result.difficulty.toLowerCase();
  const isHard = ["高", "困难", "偏难", "hard", "advanced", "复杂"].some((word) => difficultyText.includes(word));
  const focusedMinutes = sessionState?.focused_minutes ?? 0;
  const recallThresholdMinutes = 30;
  const sidePanelMode = showRecallPrompt && !recallDismissed ? "recall" : isHard ? "scaffold" : explanationMode === "exam" ? "shortcut" : "review";
  const currentTopic = result.knowledge_points[0] || course;
  const activeStrategyLabel = sessionState?.strategy_name === "cram" ? "冲刺模式" : "常规模式";
  const currentEntryId = noteEntries.length ? noteEntries[noteEntries.length - 1].id : "draft";
  const activeEditorId = activeEditorEntryId === "draft" ? currentEntryId : activeEditorEntryId;
  const displayEntries: NoteEntry[] = noteEntries;
  const hasEntries = displayEntries.length > 0;

  function hydrateThread(thread: StudyThread) {
    hydratingThreadRef.current = true;
    setInputText(thread.inputText);
    setCourse(thread.course);
    setExplanationMode(thread.explanationMode);
    setReviewMode(thread.reviewMode);
    setResult(thread.result);
    setStatus(thread.status);
    setNoteEntries(thread.noteEntries);
    setActiveEditorEntryId(thread.activeEditorEntryId || "draft");
    setFormulaDraft(thread.formulaDraft);
    setDiagramNotes(thread.diagramNotes);
    setDrawingUrl(thread.drawingUrl);
    setSessionState(thread.sessionState);
    setShowRecallPrompt(false);
    setRecallDismissed(false);
    window.setTimeout(() => {
      hydratingThreadRef.current = false;
    }, 0);
  }

  const buildThreadSnapshot = useCallback(
    (threadId: string, createdAt?: string, existingThread?: StudyThread): StudyThread => {
      const now = new Date().toISOString();
      const nextTitle =
        existingThread?.titleLocked && existingThread.title ? existingThread.title : buildThreadTitle(inputText, course, noteEntries);
      return {
        id: threadId,
        title: nextTitle,
        titleLocked: existingThread?.titleLocked ?? false,
        course,
        inputText,
        explanationMode,
        reviewMode,
        result,
        noteEntries,
        activeEditorEntryId,
        formulaDraft,
        diagramNotes,
        drawingUrl,
        sessionState,
        status,
        createdAt: createdAt || now,
        updatedAt: now,
      };
    },
    [
      inputText,
      course,
      noteEntries,
      explanationMode,
      reviewMode,
      result,
      activeEditorEntryId,
      formulaDraft,
      diagramNotes,
      drawingUrl,
      sessionState,
      status,
    ],
  );

  function openThread(threadId: string) {
    const nextThread = threads.find((thread) => thread.id === threadId);
    if (!nextThread || threadId === activeThreadId) {
      return;
    }
    if (activeThreadId) {
      const currentSnapshot = buildThreadSnapshot(
        activeThreadId,
        threads.find((thread) => thread.id === activeThreadId)?.createdAt,
        threads.find((thread) => thread.id === activeThreadId),
      );
      setThreads((current) => current.map((thread) => (thread.id === activeThreadId ? currentSnapshot : thread)));
    }
    setActiveThreadId(threadId);
    hydrateThread(nextThread);
  }

  function createNewThread() {
    const fresh = createEmptyThread(course || "电路原理");
    if (activeThreadId) {
      const currentSnapshot = buildThreadSnapshot(
        activeThreadId,
        threads.find((thread) => thread.id === activeThreadId)?.createdAt,
        threads.find((thread) => thread.id === activeThreadId),
      );
      setThreads((current) => [fresh, ...current.map((thread) => (thread.id === activeThreadId ? currentSnapshot : thread))]);
    } else {
      setThreads((current) => [fresh, ...current]);
    }
    setActiveThreadId(fresh.id);
    hydrateThread(fresh);
  }

  function renameThread(threadId: string) {
    const thread = threads.find((item) => item.id === threadId);
    if (!thread) {
      return;
    }
    const nextTitle = window.prompt("给这个线程起个名字：", thread.title)?.trim();
    if (!nextTitle) {
      return;
    }
    setThreads((current) =>
      current.map((item) =>
        item.id === threadId
          ? {
              ...item,
              title: nextTitle,
              titleLocked: true,
              updatedAt: new Date().toISOString(),
            }
          : item,
      ),
    );
  }

  function deleteThread(threadId: string) {
    const thread = threads.find((item) => item.id === threadId);
    if (!thread) {
      return;
    }
    const ok = window.confirm(`删除线程“${thread.title}”后，这个线程在左侧将消失。确定继续吗？`);
    if (!ok) {
      return;
    }
    setThreads((current) => {
      const remaining = current.filter((item) => item.id !== threadId);
      if (remaining.length) {
        const nextActive = threadId === activeThreadId ? remaining[0] : remaining.find((item) => item.id === activeThreadId) || remaining[0];
        if (nextActive) {
          setActiveThreadId(nextActive.id);
          hydrateThread(nextActive);
        }
        return remaining;
      }
      const fresh = createEmptyThread(course || "电路原理");
      setActiveThreadId(fresh.id);
      hydrateThread(fresh);
      return [fresh];
    });
  }

  const threadGroups = groupThreadsByCourse(threads);

  const sidePanel = (() => {
    if (sidePanelMode === "recall") {
      return {
        eyebrow: "暗处巧思",
        title: "侧边抽问",
        intro: `你已经累计专注 ${focusedMinutes} 分钟了，先不往下看，抽一题检查记忆回路。`,
        items: sessionState?.mini_quiz.slice(0, 3) || result.mini_quiz.slice(0, 3),
        footer: sessionState?.next_focus_prompt || result.review_schedule[0] || "先暂停 30 秒，再自己口述一遍。",
      };
    }
    if (sidePanelMode === "scaffold") {
      return {
        eyebrow: "Agent 选择",
        title: "难题支架",
        intro: "这题偏难，右侧先给你结构支架，不急着把所有信息一次看完。",
        items: [...result.solution_steps.slice(0, 3), ...result.self_questions.slice(0, 2)],
        footer: "先走通前三步，再决定是否展开完整推导。",
      };
    }
    if (sidePanelMode === "shortcut") {
      return {
        eyebrow: "Agent 选择",
        title: "考场快板",
        intro: "当前是考场优先模式，右侧只保留最该抓住的套路。",
        items: [...result.exam_tricks.slice(0, 3), ...result.formula_notes.slice(0, 2)],
        footer: "先写最稳的一步，再补完整理由。",
      };
    }
    return {
      eyebrow: "Agent 选择",
      title: "整理提醒",
      intro: "这题先以理解和整理为主，右侧给你最值得顺手记住的东西。",
      items: sessionState?.memory_tips.slice(0, 3) || result.memory_tips.slice(0, 3),
      footer: sessionState?.next_curve_prompt || result.next_action,
    };
  })();

  function scrollToEntry(entryId: string) {
    const tryScroll = (remainingAttempts: number) => {
      const target = document.getElementById(`note-entry-${entryId}`);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      if (remainingAttempts > 0) {
        window.setTimeout(() => {
          tryScroll(remainingAttempts - 1);
        }, 60);
      }
    };
    tryScroll(6);
  }

  function openEntryEditor(entryId: string) {
    if (entryId === currentEntryId) {
      return;
    }
    const entry = noteEntries.find((item) => item.id === entryId);
    if (!entry) {
      return;
    }
    setActiveEditorEntryId(entryId);
    setFormulaDraft(entry.formulaDraft);
    setDiagramNotes(entry.diagramNotes);
    setDrawingUrl(entry.drawingUrl);
    setDrawingStatus("已切换到这道题的图示编辑。");
  }

  function persistEditorState(entryId: string, patch: Partial<Pick<NoteEntry, "formulaDraft" | "diagramNotes" | "drawingUrl">>) {
    setNoteEntries((current) => current.map((entry) => (entry.id === entryId ? { ...entry, ...patch } : entry)));
  }

  async function acknowledgePrompt(triggerType: "curve" | "focus") {
    if (!sessionState?.session_key) {
      return;
    }
    try {
      const response = await fetch(`${backendUrl}/api/study-state/ack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_key: sessionState.session_key, trigger_type: triggerType }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = (await response.json()) as StudySessionState;
      setSessionState(payload);
      setNoteEntries((current) =>
        current.map((entry) =>
          entry.sessionState?.session_key === payload.session_key ? { ...entry, sessionState: payload } : entry,
        ),
      );
      if (triggerType === "focus") {
        setShowRecallPrompt(false);
        setRecallDismissed(false);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`记录复习状态失败：${message}`);
    }
  }

  function exportNote() {
    const content = [
      `题目：${inputText}`,
      `难度：${result.difficulty}`,
      "",
      "知识点：",
      ...result.knowledge_points.map((item) => `- ${item}`),
      "",
      "解题步骤：",
      ...result.solution_steps.map((item, index) => `${index + 1}. ${item}`),
      "",
      "公式与套路：",
      ...result.formula_notes.map((item) => `- ${item}`),
      "",
      "小白讲解：",
      result.novice_explain,
      "",
      "讲解：",
      result.explanation,
      "",
      "例题：",
      ...result.examples.map((item) => `- ${item}`),
      "",
      "错题变种：",
      ...result.variant_questions.map((item) => `- ${item}`),
      "",
      "小测题：",
      ...result.mini_quiz.map((item) => `- ${item}`),
      "",
      "考点提示：",
      ...result.exam_focus_prediction.map((item) => `- ${item}`),
      "",
      "得分拆解：",
      ...result.score_breakdown.map((item) => `- ${item}`),
      "",
      `下一步：${result.next_action}`,
      "",
      `信心提示：${result.confidence_note}`,
      "",
      `风险提示：${result.risk_notice}`,
      "",
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, "examnova-study-note.txt");
  }

  function exportLines(filename: string, title: string, items: string[]) {
    const content = [title, ...items.map((item) => `- ${item}`), ""].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, filename);
  }

  function exportWrongbook() {
    const content = wrongbookItems
      .map(
        (item) =>
          `${item.timestamp}｜${item.course || "课程"}｜${item.difficulty || "难度"}\n题目：${item.question_text}\n摘要：${
            item.summary
          }\n知识点：${item.knowledge_points.join("、")}`,
      )
      .join("\n\n");
    const blob = new Blob([content || "暂无错题本记录。"], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, "examnova-wrongbook.txt");
  }

  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function escapeHtml(text: string) {
    return text
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function buildExportCss(tone: "color" | "bw") {
    const base = `
      :root { color-scheme: light; }
      body {
        font-family: "Noto Serif SC", "Noto Serif", "Source Han Serif SC", "SimSun", serif;
        margin: 28px;
        color: #2c241a;
        background: #ffffff;
      }
      h1 { font-size: 24px; margin: 0 0 8px; }
      h2 { font-size: 16px; margin: 18px 0 6px; }
      p, li { font-size: 13px; line-height: 1.7; }
      ul, ol { padding-left: 20px; }
      .meta { color: #6b6256; }
      .card {
        border: 1px solid #e7dfd3;
        border-radius: 12px;
        padding: 10px 12px;
        background: #fdfaf4;
        margin: 10px 0;
      }
      body.bw, body.bw * {
        color: #111111 !important;
        background: #ffffff !important;
      }
      body.bw .card { border-color: #111111; }
      @media print {
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        body.bw { -webkit-print-color-adjust: economy; print-color-adjust: economy; }
      }
    `;
    return tone === "bw" ? base : base;
  }

  function buildDocHtml(title: string, body: string, tone: "color" | "bw") {
    const className = tone === "bw" ? "bw" : "";
    return `
      <!doctype html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>${escapeHtml(title)}</title>
          <style>${buildExportCss(tone)}</style>
        </head>
        <body class="${className}">
          ${body}
        </body>
      </html>
    `.trim();
  }

  function openPrintDocument(html: string, onError: () => void) {
    const printWindow = window.open("", "_blank", "width=900,height=700");
    if (!printWindow) {
      onError();
      return;
    }
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  }

  function exportNoteDoc(format: "word" | "pdf", tone: "color" | "bw") {
    const body = `
      <h1>ExamNova 学习笔记</h1>
      <p class="meta">题目：${escapeHtml(inputText)}</p>
      <p class="meta">课程：${escapeHtml(course)} | 难度：${escapeHtml(result.difficulty)}</p>
      <div class="card">
        <h2>知识点</h2>
        <ul>${result.knowledge_points.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>解题步骤</h2>
        <ol>${result.solution_steps.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
      </div>
      <div class="card">
        <h2>公式与套路</h2>
        <ul>${result.formula_notes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>小白讲解</h2>
        <p>${escapeHtml(result.novice_explain)}</p>
      </div>
      <div class="card">
        <h2>讲解</h2>
        <p>${escapeHtml(result.explanation)}</p>
      </div>
      <div class="card">
        <h2>例题</h2>
        <ul>${result.examples.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>错题变种</h2>
        <ul>${result.variant_questions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>小测题</h2>
        <ul>${result.mini_quiz.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>考点提示</h2>
        <ul>${result.exam_focus_prediction.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>得分拆解</h2>
        <ul>${result.score_breakdown.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <p><strong>下一步：</strong>${escapeHtml(result.next_action)}</p>
      <p><strong>信心提示：</strong>${escapeHtml(result.confidence_note)}</p>
      <p><strong>风险提示：</strong>${escapeHtml(result.risk_notice)}</p>
    `.trim();
    const html = buildDocHtml("ExamNova 学习笔记", body, tone);
    if (format === "word") {
      const suffix = tone === "bw" ? "-bw" : "";
      downloadBlob(new Blob([html], { type: "application/msword" }), `examnova-study-note${suffix}.doc`);
      return;
    }
    openPrintDocument(html, () => {
      setStatus("PDF 导出失败：浏览器阻止了弹窗。");
    });
  }

  function exportWrongbookDoc(format: "word" | "pdf", tone: "color" | "bw") {
    const itemsHtml = wrongbookItems
      .map(
        (item) => `
        <div class="card">
          <h2>${escapeHtml(item.timestamp)}</h2>
          <p><strong>题目：</strong>${escapeHtml(item.question_text)}</p>
          <p class="meta">课程：${escapeHtml(item.course || "课程")} | 难度：${escapeHtml(
            item.difficulty || "难度",
          )}</p>
          <p><strong>摘要：</strong>${escapeHtml(item.summary)}</p>
          <ul>${item.knowledge_points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
        </div>
      `,
      )
      .join("");
    const body = `
      <h1>ExamNova 错题本</h1>
      ${itemsHtml || "<p>暂无错题记录。</p>"}
    `.trim();
    const html = buildDocHtml("ExamNova 错题本", body, tone);
    if (format === "word") {
      const suffix = tone === "bw" ? "-bw" : "";
      downloadBlob(new Blob([html], { type: "application/msword" }), `examnova-wrongbook${suffix}.doc`);
      return;
    }
    openPrintDocument(html, () => {
      setWrongbookStatus("PDF 导出失败：浏览器阻止了弹窗。");
    });
  }

  function exportNoteMarkdown() {
    const lines = [
      "# ExamNova 学习笔记",
      "",
      `题目：${inputText}`,
      `课程：${course}`,
      `难度：${result.difficulty}`,
      "",
      "## 知识点",
      ...result.knowledge_points.map((item) => `- ${item}`),
      "",
      "## 解题步骤",
      ...result.solution_steps.map((item, index) => `${index + 1}. ${item}`),
      "",
      "## 公式与套路",
      ...result.formula_notes.map((item) => `- ${item}`),
      "",
      "## 小白讲解",
      result.novice_explain,
      "",
      "## 讲解",
      result.explanation,
      "",
      "## 例题",
      ...result.examples.map((item) => `- ${item}`),
      "",
      "## 错题变种",
      ...result.variant_questions.map((item) => `- ${item}`),
      "",
      "## 小测题",
      ...result.mini_quiz.map((item) => `- ${item}`),
      "",
      "## 考点提示",
      ...result.exam_focus_prediction.map((item) => `- ${item}`),
      "",
      "## 得分拆解",
      ...result.score_breakdown.map((item) => `- ${item}`),
      "",
      `下一步：${result.next_action}`,
      "",
      `信心提示：${result.confidence_note}`,
      "",
      `风险提示：${result.risk_notice}`,
      "",
    ];
    downloadBlob(new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" }), "examnova-study-note.md");
  }

  function exportNoteWord() {
    exportNoteDoc("word", "color");
    const useLegacy = false;
    if (!useLegacy) {
      return;
    }
    const html = `
      <html>
        <head><meta charset="utf-8"></head>
        <body>
          <h1>ExamNova 学习笔记</h1>
          <p><strong>题目：</strong>${escapeHtml(inputText)}</p>
          <p><strong>课程：</strong>${escapeHtml(course)}</p>
          <p><strong>难度：</strong>${escapeHtml(result.difficulty)}</p>
          <h2>知识点</h2>
          <ul>${result.knowledge_points.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>解题步骤</h2>
          <ol>${result.solution_steps.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
          <h2>公式与套路</h2>
          <ul>${result.formula_notes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>小白讲解</h2>
          <p>${escapeHtml(result.novice_explain)}</p>
          <h2>讲解</h2>
          <p>${escapeHtml(result.explanation)}</p>
          <h2>例题</h2>
          <ul>${result.examples.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>错题变种</h2>
          <ul>${result.variant_questions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>小测题</h2>
          <ul>${result.mini_quiz.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>考点提示</h2>
          <ul>${result.exam_focus_prediction.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>得分拆解</h2>
          <ul>${result.score_breakdown.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <p><strong>下一步：</strong>${escapeHtml(result.next_action)}</p>
          <p><strong>信心提示：</strong>${escapeHtml(result.confidence_note)}</p>
          <p><strong>风险提示：</strong>${escapeHtml(result.risk_notice)}</p>
        </body>
      </html>
    `.trim();
    downloadBlob(new Blob([html], { type: "application/msword" }), "examnova-study-note.doc");
  }

  function exportNotePdf() {
    exportNoteDoc("pdf", "color");
    const useLegacy = false;
    if (!useLegacy) {
      return;
    }
    const html = `
      <html>
        <head><meta charset="utf-8"><title>ExamNova 学习笔记</title></head>
        <body>
          <h1>ExamNova 学习笔记</h1>
          <p><strong>题目：</strong>${escapeHtml(inputText)}</p>
          <p><strong>课程：</strong>${escapeHtml(course)}</p>
          <p><strong>难度：</strong>${escapeHtml(result.difficulty)}</p>
          <h2>知识点</h2>
          <ul>${result.knowledge_points.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>解题步骤</h2>
          <ol>${result.solution_steps.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
          <h2>公式与套路</h2>
          <ul>${result.formula_notes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>小白讲解</h2>
          <p>${escapeHtml(result.novice_explain)}</p>
          <h2>讲解</h2>
          <p>${escapeHtml(result.explanation)}</p>
          <h2>例题</h2>
          <ul>${result.examples.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>错题变种</h2>
          <ul>${result.variant_questions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>小测题</h2>
          <ul>${result.mini_quiz.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>考点提示</h2>
          <ul>${result.exam_focus_prediction.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <h2>得分拆解</h2>
          <ul>${result.score_breakdown.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
          <p><strong>下一步：</strong>${escapeHtml(result.next_action)}</p>
          <p><strong>信心提示：</strong>${escapeHtml(result.confidence_note)}</p>
          <p><strong>风险提示：</strong>${escapeHtml(result.risk_notice)}</p>
        </body>
      </html>
    `.trim();
    const printWindow = window.open("", "_blank", "width=900,height=700");
    if (!printWindow) {
      setStatus("PDF 导出失败：浏览器阻止了弹窗。");
      return;
    }
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  }

  function exportWrongbookMarkdown() {
    const lines = ["# ExamNova 错题本", ""];
    if (!wrongbookItems.length) {
      lines.push("暂无错题记录。");
    } else {
      wrongbookItems.forEach((item) => {
        lines.push(`## ${item.timestamp}`);
        lines.push(`题目：${item.question_text}`);
        lines.push(`课程：${item.course || "课程"} | 难度：${item.difficulty || "难度"}`);
        lines.push(`摘要：${item.summary}`);
        lines.push("知识点：");
        lines.push(...item.knowledge_points.map((point) => `- ${point}`));
        lines.push("");
      });
    }
    downloadBlob(new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" }), "examnova-wrongbook.md");
  }

  function exportWrongbookWord() {
    exportWrongbookDoc("word", "color");
    const useLegacy = false;
    if (!useLegacy) {
      return;
    }
    const itemsHtml = wrongbookItems
      .map(
        (item) => `
        <section>
          <h2>${escapeHtml(item.timestamp)}</h2>
          <p><strong>题目：</strong>${escapeHtml(item.question_text)}</p>
          <p><strong>课程：</strong>${escapeHtml(item.course || "课程")} | <strong>难度：</strong>${escapeHtml(
            item.difficulty || "难度",
          )}</p>
          <p><strong>摘要：</strong>${escapeHtml(item.summary)}</p>
          <ul>${item.knowledge_points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
        </section>
      `,
      )
      .join("");
    const html = `
      <html>
        <head><meta charset="utf-8"></head>
        <body>
          <h1>ExamNova 错题本</h1>
          ${itemsHtml || "<p>暂无错题记录。</p>"}
        </body>
      </html>
    `.trim();
    downloadBlob(new Blob([html], { type: "application/msword" }), "examnova-wrongbook.doc");
  }

  function exportWrongbookPdf() {
    exportWrongbookDoc("pdf", "color");
    const useLegacy = false;
    if (!useLegacy) {
      return;
    }
    const itemsHtml = wrongbookItems
      .map(
        (item) => `
        <section>
          <h2>${escapeHtml(item.timestamp)}</h2>
          <p><strong>题目：</strong>${escapeHtml(item.question_text)}</p>
          <p><strong>课程：</strong>${escapeHtml(item.course || "课程")} | <strong>难度：</strong>${escapeHtml(
            item.difficulty || "难度",
          )}</p>
          <p><strong>摘要：</strong>${escapeHtml(item.summary)}</p>
          <ul>${item.knowledge_points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
        </section>
      `,
      )
      .join("");
    const html = `
      <html>
        <head><meta charset="utf-8"><title>ExamNova 错题本</title></head>
        <body>
          <h1>ExamNova 错题本</h1>
          ${itemsHtml || "<p>暂无错题记录。</p>"}
        </body>
      </html>
    `.trim();
    const printWindow = window.open("", "_blank", "width=900,height=700");
    if (!printWindow) {
      setWrongbookStatus("PDF 导出失败：浏览器阻止了弹窗。");
      return;
    }
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  }

  function exportNoteWordBw() {
    exportNoteDoc("word", "bw");
  }

  function exportNotePdfBw() {
    exportNoteDoc("pdf", "bw");
  }

  function exportWrongbookWordBw() {
    exportWrongbookDoc("word", "bw");
  }

  function exportWrongbookPdfBw() {
    exportWrongbookDoc("pdf", "bw");
  }

  function renderFormula() {
    try {
      const html = katex.renderToString(formulaDraft || "\\ ", {
        throwOnError: false,
        displayMode: true,
      });
      return { html, error: "" };
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      return { html: "", error: message };
    }
  }

  const syncCanvasSize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) {
      return;
    }
    const nextWidth = Math.round(width * ratio);
    const nextHeight = Math.round(height * ratio);
    if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
      canvas.width = nextWidth;
      canvas.height = nextHeight;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      if (drawingUrl) {
        const image = new Image();
        image.onload = () => {
          context.clearRect(0, 0, width, height);
          context.drawImage(image, 0, 0, width, height);
        };
        image.src = drawingUrl;
      } else {
        context.clearRect(0, 0, width, height);
      }
    }
  }, [drawingUrl]);

  function saveDrawingSnapshot() {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const dataUrl = canvas.toDataURL("image/png");
    setDrawingUrl(dataUrl);
    persistEditorState(activeEditorId, { drawingUrl: dataUrl });
    setDrawingStatus("绘图内容已更新。");
  }

  function clearDrawing() {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
    setDrawingUrl(null);
    persistEditorState(activeEditorId, { drawingUrl: null });
    setDrawingStatus("已清空绘图区。");
  }

  function exportDrawing() {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const dataUrl = canvas.toDataURL("image/png");
    const anchor = document.createElement("a");
    anchor.href = dataUrl;
    anchor.download = "examnova-diagram.png";
    anchor.click();
  }

  function getCanvasPoint(event: ReactPointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) {
      return null;
    }
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function beginDrawing(event: ReactPointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    const point = getCanvasPoint(event);
    if (!context || !point) {
      return;
    }
    drawingRef.current = true;
    lastPointRef.current = point;
    canvas.setPointerCapture(event.pointerId);
    context.strokeStyle = drawingColor;
    context.lineWidth = drawingWidth;
    context.lineCap = "round";
    context.beginPath();
    context.moveTo(point.x, point.y);
  }

  function drawMove(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) {
      return;
    }
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    const point = getCanvasPoint(event);
    if (!context || !point) {
      return;
    }
    context.lineTo(point.x, point.y);
    context.stroke();
    lastPointRef.current = point;
  }

  function endDrawing(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) {
      return;
    }
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (context) {
      context.closePath();
    }
    drawingRef.current = false;
    lastPointRef.current = null;
    canvas?.releasePointerCapture(event.pointerId);
    saveDrawingSnapshot();
  }

  const fetchWrongbook = useCallback(async () => {
    setWrongbookStatus("正在加载错题本...");
    try {
      const response = await fetch(`${backendUrl}/api/wrongbook/recent?limit=6`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = (await response.json()) as { items: WrongbookItem[] };
      setWrongbookItems(payload.items);
      setWrongbookStatus(payload.items.length ? "错题本已更新。" : "错题本暂无记录。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setWrongbookStatus(`错题本读取失败：${message}`);
    }
  }, [backendUrl]);

  async function addToWrongbook() {
    setWrongbookStatus("正在加入错题本...");
    try {
      const summary = result.explanation || inputText;
      const response = await fetch(`${backendUrl}/api/wrongbook/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_text: inputText,
          summary,
          course,
          difficulty: result.difficulty,
          knowledge_points: result.knowledge_points,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      await fetchWrongbook();
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setWrongbookStatus(`加入失败：${message}`);
    }
  }

  useEffect(() => {
    void fetchWrongbook();
  }, [fetchWrongbook]);

  useEffect(() => {
    const raw = window.localStorage.getItem(THREADS_STORAGE_KEY);
    let savedThreads: StudyThread[] = [];
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as StudyThread[];
        if (Array.isArray(parsed)) {
          savedThreads = parsed;
        }
      } catch {
        savedThreads = [];
      }
    }

    let nextThreads = savedThreads;
    let nextActive = savedThreads[0]?.id ?? "";

    const existingEmpty = savedThreads.find((thread) => isThreadEmpty(thread));
    if (existingEmpty) {
      nextActive = existingEmpty.id;
    } else {
      const fresh = createEmptyThread(savedThreads[0]?.course || "电路原理");
      nextThreads = [fresh, ...savedThreads];
      nextActive = fresh.id;
    }

    if (!nextThreads.length) {
      const fresh = createEmptyThread();
      nextThreads = [fresh];
      nextActive = fresh.id;
    }

    setThreads(nextThreads);
    setActiveThreadId(nextActive);
    const activeThread = nextThreads.find((thread) => thread.id === nextActive) || nextThreads[0];
    if (activeThread) {
      hydrateThread(activeThread);
    }
    threadsReadyRef.current = true;
  }, [backendUrl]);

  useEffect(() => {
    if (!threadsReadyRef.current || importedHistoryRef.current || threads.length !== 1 || !isThreadEmpty(threads[0])) {
      return;
    }
    importedHistoryRef.current = true;
    void (async () => {
      try {
        const response = await fetch(`${backendUrl}/api/study-notes/recent?limit=10`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = (await response.json()) as {
          items: Array<{
            timestamp: string;
            course: string;
            question_text: string;
            session_key: string | null;
            result: StudyResponse;
          }>;
        };
        const recentEntries = payload.items
          .map((item, index) => ({
            id: item.session_key || `recent-${index + 1}`,
            questionText: item.question_text,
            course: item.course,
            result: item.result,
            sessionState: null,
            formulaDraft: buildFormulaDraft(item.result),
            diagramNotes: buildDiagramNotes(item.result),
            drawingUrl: null,
          }))
          .filter((entry) => !looksLikeBrokenArchiveText(entry.questionText) && !looksLikeBrokenArchiveText(entry.course));
        if (!recentEntries.length) {
          return;
        }
        setThreads((current) => [...current, createImportedThread(recentEntries)]);
      } catch {
        // Keep the new thread experience clean even if history import fails.
      }
    })();
  }, [backendUrl, threads]);

  useEffect(() => {
    if (!threadsReadyRef.current || hydratingThreadRef.current || !activeThreadId) {
      return;
    }
    setThreads((current) => {
      const index = current.findIndex((thread) => thread.id === activeThreadId);
      if (index === -1) {
        return current;
      }
      const existing = current[index];
      const next = buildThreadSnapshot(activeThreadId, existing.createdAt, existing);
      const existingComparable = JSON.stringify({ ...existing, updatedAt: "" });
      const nextComparable = JSON.stringify({ ...next, updatedAt: "" });
      if (existingComparable === nextComparable) {
        return current;
      }
      const clone = [...current];
      clone[index] = next;
      return clone;
    });
  }, [
    activeThreadId,
    buildThreadSnapshot,
  ]);

  useEffect(() => {
    if (!threadsReadyRef.current) {
      return;
    }
    window.localStorage.setItem(THREADS_STORAGE_KEY, JSON.stringify(threads));
  }, [threads]);

  useEffect(() => {
    const entry = noteEntries.find((item) => item.id === activeEditorId);
    if (!entry) {
      return;
    }
    setFormulaDraft(entry.formulaDraft);
    setDiagramNotes(entry.diagramNotes);
    setDrawingUrl(entry.drawingUrl);
  }, [activeEditorId, noteEntries]);

  useEffect(() => {
    persistEditorState(activeEditorId, { formulaDraft });
  }, [activeEditorId, formulaDraft]);

  useEffect(() => {
    persistEditorState(activeEditorId, { diagramNotes });
  }, [activeEditorId, diagramNotes]);

  useEffect(() => {
    syncCanvasSize();
    const handleResize = () => {
      syncCanvasSize();
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [syncCanvasSize]);

  useEffect(() => {
    if (!drawingUrl) {
      return;
    }
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      return;
    }
    const image = new Image();
    image.onload = () => {
      context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
      context.drawImage(image, 0, 0, canvas.clientWidth, canvas.clientHeight);
    };
    image.src = drawingUrl;
  }, [drawingUrl]);

  useEffect(() => {
    if (!sessionState) {
      return;
    }
    if (!recallDismissed && (sessionState.focus_due_count > 0 || focusedMinutes >= recallThresholdMinutes)) {
      setShowRecallPrompt(true);
    }
  }, [focusedMinutes, recallDismissed, recallThresholdMinutes, sessionState]);

  useEffect(() => {
    if (!sessionState?.session_key) {
      return;
    }

    const heartbeat = async () => {
      if (document.visibilityState === "hidden") {
        return;
      }
      try {
        const response = await fetch(`${backendUrl}/api/study-state/heartbeat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_key: sessionState.session_key, active_seconds: 60 }),
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = (await response.json()) as StudySessionState;
        setSessionState(payload);
        setNoteEntries((current) =>
          current.map((entry) =>
            entry.sessionState?.session_key === payload.session_key ? { ...entry, sessionState: payload } : entry,
          ),
        );
      } catch {
        // Keep the page readable even if heartbeat fails temporarily.
      }
    };

    const timer = window.setInterval(() => {
      void heartbeat();
    }, 60000);

    return () => {
      window.clearInterval(timer);
    };
  }, [backendUrl, sessionState?.session_key]);

  async function syncStudySession(nextResult: StudyResponse, questionText: string) {
    const response = await fetch(`${backendUrl}/api/study-state/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course,
        question_text: questionText,
        topic_label: nextResult.knowledge_points[0] || course,
        knowledge_points: nextResult.knowledge_points,
        mini_quiz: nextResult.mini_quiz,
        memory_tips: nextResult.memory_tips,
        review_mode: reviewMode,
        explanation_mode: explanationMode,
        difficulty: nextResult.difficulty,
      }),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = (await response.json()) as StudySessionState;
    setSessionState(payload);
    setShowRecallPrompt(payload.focus_due_count > 0);
    setRecallDismissed(false);
    return payload;
  }

  async function saveStudyNote(questionText: string, nextResult: StudyResponse, sessionKey: string | null) {
    await fetch(`${backendUrl}/api/study-notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course,
        question_text: questionText,
        session_key: sessionKey,
        result: nextResult,
      }),
    });
  }

  function applyResultToEntry(entryId: string, nextResult: StudyResponse, previousResult: StudyResponse) {
    const nextFormulaDraft = buildFormulaDraft(nextResult);
    const nextDiagramNotes = buildDiagramNotes(nextResult);
    const previousFormulaDraft = buildFormulaDraft(previousResult);
    const previousDiagramNotes = buildDiagramNotes(previousResult);

    setNoteEntries((current) =>
      current.map((entry) => {
        if (entry.id !== entryId) {
          return entry;
        }
        const shouldRefreshFormula = !entry.formulaDraft.trim() || entry.formulaDraft === previousFormulaDraft;
        const shouldRefreshDiagram = !entry.diagramNotes.trim() || entry.diagramNotes === previousDiagramNotes;
        return {
          ...entry,
          result: nextResult,
          formulaDraft: shouldRefreshFormula ? nextFormulaDraft : entry.formulaDraft,
          diagramNotes: shouldRefreshDiagram ? nextDiagramNotes : entry.diagramNotes,
        };
      }),
    );

    setResult(nextResult);
    if (activeEditorId === entryId) {
      if (!formulaDraft.trim() || formulaDraft === previousFormulaDraft) {
        setFormulaDraft(nextFormulaDraft);
      }
      if (!diagramNotes.trim() || diagramNotes === previousDiagramNotes) {
        setDiagramNotes(nextDiagramNotes);
      }
    }
  }

  async function enrichStudyEntry(entryId: string, questionText: string, coreResult: StudyResponse, sessionKey: string | null) {
    try {
      const response = await fetch(`${backendUrl}/api/study/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_text: questionText,
          explanation_mode: explanationMode,
          course,
          detail_level: "full",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const enriched = (await response.json()) as StudyResponse;
      applyResultToEntry(entryId, enriched, coreResult);
      await syncStudySession(enriched, questionText);
      await saveStudyNote(questionText, enriched, sessionKey);
      setStatus("主解已生成，侧栏补充已更新。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`主解已生成，补充内容更新失败：${message}`);
    }
  }

  async function handleAnalyze(overrideText?: string) {
    setStatus("正在生成主解...");

    try {
      const textToUse = overrideText ?? inputText;
      if (!textToUse.trim()) {
        setStatus("请先输入题目内容。");
        return;
      }
      const response = await fetch(`${backendUrl}/api/agent/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: "study",
          payload: {
            input_text: textToUse,
            explanation_mode: explanationMode,
            course,
            detail_level: "core",
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = (await response.json()) as { result: StudyResponse };
      setResult(payload.result);
      const nextFormulaDraft = buildFormulaDraft(payload.result);
      const nextDiagramNotes = buildDiagramNotes(payload.result);
      setFormulaDraft(nextFormulaDraft);
      setDiagramNotes(nextDiagramNotes);
      setDrawingUrl(null);
      const session = await syncStudySession(payload.result, textToUse);
      await saveStudyNote(textToUse, payload.result, session?.session_key ?? null);
      const entryId = session?.session_key || `${Date.now()}-${noteEntries.length + 1}`;
      setNoteEntries((current) => [
        ...current,
        {
          id: entryId,
          questionText: textToUse,
          course,
          result: payload.result,
          sessionState: session,
          formulaDraft: nextFormulaDraft,
          diagramNotes: nextDiagramNotes,
          drawingUrl: null,
        },
      ]);
      setActiveEditorEntryId(entryId);
      setStatus("主解已生成，正在补充图解、小测和复习建议...");
      scrollToEntry(entryId);
      void enrichStudyEntry(entryId, textToUse, payload.result, session?.session_key ?? null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`学习请求失败：${message}`);
    }
  }

  async function handleOcr() {
    if (!ocrFile) {
      setOcrStatus("请先选择图片文件。");
      return;
    }

    setOcrStatus("正在识别图片...");
    const form = new FormData();
    form.append("file", ocrFile);

    try {
      const response = await fetch(`${backendUrl}/api/ocr/parse`, {
        method: "POST",
        body: form,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = (await response.json()) as { text: string; filename: string; engine: string };
      setInputText(payload.text);
      setOcrStatus(`OCR 已返回（${payload.engine}）：${payload.filename}`);
      await handleAnalyze(payload.text);
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setOcrStatus(`OCR 失败：${message}`);
    }
  }

  return (
    <>
      <section className={styles.studyCanvas}>
        <div className={styles.a4Stage}>
          <div className={styles.studyWorkbench}>
            <aside className={styles.archiveRail}>
              <article className={styles.archiveRailCard}>
                <div className={styles.threadRailHeader}>
                  <div>
                    <span className={styles.agentRailEyebrow}>工作线程</span>
                    <h3 className={styles.archiveRailTitle}>学习页面</h3>
                  </div>
                  <button className={styles.secondary} onClick={createNewThread}>
                    新线程
                  </button>
                </div>
                <div className={styles.threadList}>
                  {threadGroups.map((group) => (
                    <section key={group.courseName} className={styles.threadGroup}>
                      <div className={styles.threadGroupTitle}>{group.courseName}</div>
                      {group.items.map((thread) => (
                        <div
                          key={thread.id}
                          className={`${styles.threadItem} ${thread.id === activeThreadId ? styles.threadItemActive : ""}`}
                        >
                          <button className={styles.threadItemMain} onClick={() => openThread(thread.id)}>
                            <strong className={styles.threadItemTitle}>{thread.title}</strong>
                            <span className={styles.threadItemMeta}>{formatThreadTime(thread.updatedAt)}</span>
                          </button>
                          <div className={styles.threadItemActions}>
                            <button
                              className={styles.threadAction}
                              type="button"
                              onClick={() => renameThread(thread.id)}
                              aria-label={`重命名 ${thread.title}`}
                            >
                              改名
                            </button>
                            <button
                              className={styles.threadAction}
                              type="button"
                              onClick={() => deleteThread(thread.id)}
                              aria-label={`删除 ${thread.title}`}
                            >
                              删除
                            </button>
                          </div>
                        </div>
                      ))}
                    </section>
                  ))}
                </div>
              </article>

              <article className={styles.archiveRailCard}>
                <span className={styles.agentRailEyebrow}>课程归档</span>
                <h3 className={styles.archiveRailTitle}>{course}</h3>
                <p className={styles.archiveRailText}>主题：{currentTopic}</p>
                <p className={styles.archiveRailText}>
                  {hasEntries ? "当前纸面会持续向下延长，新的题目会接在下面。" : "这是一个新的空白页面，可以按课程单独整理这一轮题目。"}
                </p>
              </article>

              <article className={styles.archiveRailCard}>
                <span className={styles.agentRailEyebrow}>纸面目录</span>
                <div className={styles.archiveSectionList}>
                  {displayEntries.map((entry, index) => (
                    <button
                      key={entry.id}
                      className={styles.archiveJump}
                      onClick={() => {
                        openEntryEditor(entry.id);
                        scrollToEntry(entry.id);
                      }}
                    >
                      {buildArchiveLabel(entry, index)}
                    </button>
                  ))}
                </div>
              </article>

              <article className={styles.archiveRailCard}>
                <span className={styles.agentRailEyebrow}>知识归档</span>
                <ul className={styles.agentRailList}>
                  {result.knowledge_points.length ? (
                    result.knowledge_points.map((item) => <li key={item}>{item}</li>)
                  ) : (
                    <li>等待分析后生成知识点归档。</li>
                  )}
                </ul>
              </article>

              <details className={styles.agentRailCollapse}>
                <summary>导出与整理</summary>
                <div className={styles.agentRailCollapseBody}>
                  <div className={styles.archiveExportGrid}>
                    <button className={styles.secondary} onClick={exportNote}>
                      导出 TXT
                    </button>
                    <button className={styles.secondary} onClick={exportNoteMarkdown}>
                      导出 MD
                    </button>
                    <button className={styles.secondary} onClick={exportNotePdf}>
                      导出 PDF
                    </button>
                    <button className={styles.secondary} onClick={addToWrongbook}>
                      加入错题本
                    </button>
                  </div>
                </div>
              </details>
            </aside>

            <div className={`${styles.notePaper} ${styles.a4Sheet}`}>
              {!hasEntries ? (
                <article className={`${styles.noteEntry} ${styles.noteEntryEmpty}`}>
                  <div className={styles.cornellToolbar}>
                    <span className={styles.noteKicker}>Cornell-style study note</span>
                  </div>
                  <header className={styles.noteHeader}>
                    <h2 className={styles.noteTitle}>新页面</h2>
                    <p className={styles.noteQuestion}>这一页还没有题目。你可以在底部输入一道题，按课程单独开启这一轮学习。</p>
                  </header>
                  <section className={`${styles.cornellSection} ${styles.cornellSectionStrong}`}>
                    <h3 className={styles.cornellSectionTitle}>建议</h3>
                    <div className={styles.cornellBodyText}>
                      先确认课程，再把一道题发进来。这个线程会保留你这一门课的整张纸面，方便后面继续翻看和导出。
                    </div>
                  </section>
                </article>
              ) : (
                displayEntries.map((entry, index) => {
                const isCurrentEntry = entry.id === currentEntryId;
                const entryFocusedMinutes = entry.sessionState?.focused_minutes ?? 0;
                const entryWallMinutes = entry.sessionState?.wall_elapsed_minutes ?? 0;
                return (
                  <article key={entry.id} id={`note-entry-${entry.id}`} className={styles.noteEntry}>
                    {index === 0 ? (
                      <div className={styles.cornellToolbar}>
                        <span className={styles.noteKicker}>Cornell-style study note</span>
                        <button className={styles.secondary} onClick={exportNoteWord}>
                          导出 Word
                        </button>
                        <button className={styles.secondary} onClick={exportNotePdfBw}>
                          导出黑白稿
                        </button>
                      </div>
                    ) : null}

                    <header className={styles.noteHeader} ref={isCurrentEntry ? questionRef : undefined}>
                      <h2 className={styles.noteTitle}>题目 {index + 1}</h2>
                      <p className={styles.noteQuestion}>{entry.questionText}</p>
                    </header>

                    <div className={styles.cornellMain}>
                      <section className={styles.noteMetaBar}>
                        <article className={styles.noteMetaCard}>
                          <span className={styles.noteMetaLabel}>课程</span>
                          <p className={styles.noteMetaValue}>{entry.course}</p>
                        </article>
                        <article className={styles.noteMetaCard}>
                          <span className={styles.noteMetaLabel}>难度</span>
                          <p className={styles.noteMetaValue}>{entry.result.difficulty}</p>
                        </article>
                        <article className={styles.noteMetaCard}>
                          <span className={styles.noteMetaLabel}>学习</span>
                          <p className={styles.noteMetaValue}>
                            {entry.sessionState ? `${entryFocusedMinutes} 分钟专注 / ${entryWallMinutes} 分钟间隔` : "刚开始"}
                          </p>
                        </article>
                      </section>

                      <section
                        ref={isCurrentEntry ? explanationRef : undefined}
                        className={`${styles.cornellSection} ${styles.cornellSectionStrong}`}
                      >
                        <h3 className={styles.cornellSectionTitle}>讲解</h3>
                        <div
                          className={styles.cornellBodyText}
                          dangerouslySetInnerHTML={{ __html: renderMathText(entry.result.explanation) }}
                        />
                      </section>

                      <section
                        ref={isCurrentEntry ? solutionRef : undefined}
                        className={`${styles.cornellSection} ${styles.cornellSectionTall}`}
                      >
                        <h3 className={styles.cornellSectionTitle}>解题</h3>
                        <ol className={styles.cornellOrdered}>
                          {entry.result.solution_steps.map((item, idx) => (
                            <li key={`${entry.id}-step-${idx}`} dangerouslySetInnerHTML={{ __html: renderMathText(item) }} />
                          ))}
                        </ol>
                        <details className={styles.inlineSecret}>
                          <summary>图解</summary>
                          <div className={styles.inlineSecretBody}>
                            <p className={styles.hint} dangerouslySetInnerHTML={{ __html: renderMathText(entry.result.diagram_hint) }} />
                            {isCurrentEntry ? (
                              <>
                                <div className={styles.field}>
                                  <label className={styles.label}>图解说明</label>
                                  <textarea
                                    className={styles.textarea}
                                    value={diagramNotes}
                                    onChange={(event) => setDiagramNotes(event.target.value)}
                                    placeholder="给图加一句图注、方向说明或注释。"
                                  />
                                </div>
                                <div className={styles.canvasToolbar}>
                                  <label className={styles.canvasLabel}>
                                    线宽
                                    <input
                                      className={styles.range}
                                      type="range"
                                      min={1}
                                      max={6}
                                      value={drawingWidth}
                                      onChange={(event) => setDrawingWidth(Number(event.target.value))}
                                    />
                                  </label>
                                  <label className={styles.canvasLabel}>
                                    颜色
                                    <input
                                      className={styles.color}
                                      type="color"
                                      value={drawingColor}
                                      onChange={(event) => setDrawingColor(event.target.value)}
                                    />
                                  </label>
                                  <button className={styles.secondary} onClick={clearDrawing}>
                                    清空
                                  </button>
                                  <button className={styles.secondary} onClick={exportDrawing}>
                                    导出图
                                  </button>
                                </div>
                                <div className={styles.canvasWrap}>
                                  <canvas
                                    ref={canvasRef}
                                    className={styles.canvas}
                                    onPointerDown={beginDrawing}
                                    onPointerMove={drawMove}
                                    onPointerUp={endDrawing}
                                    onPointerLeave={endDrawing}
                                  />
                                </div>
                                <div className={styles.statusLine}>{drawingStatus}</div>
                              </>
                            ) : (
                              <>
                                {entry.drawingUrl ? (
                                  <NextImage
                                    className={styles.diagramPreview}
                                    src={entry.drawingUrl}
                                    alt="题目图示预览"
                                    width={640}
                                    height={360}
                                    unoptimized
                                  />
                                ) : (
                                <p className={styles.hint}>这道题目前没有单独图解，你可以按需要补画和标注。</p>
                              )}
                                <p className={styles.hint} dangerouslySetInnerHTML={{ __html: renderMathText(entry.diagramNotes) }} />
                                <button className={styles.secondary} onClick={() => openEntryEditor(entry.id)}>
                                  编辑这题图解
                                </button>
                              </>
                            )}
                          </div>
                        </details>
                      </section>

                      <section
                        ref={isCurrentEntry ? shortcutRef : undefined}
                        className={`${styles.cornellSection} ${styles.cornellSectionTall}`}
                      >
                        <h3 className={styles.cornellSectionTitle}>快速解题</h3>
                        <ul className={styles.cornellFormulaList}>
                          {[...entry.result.formula_notes, ...entry.result.exam_tricks].map((item, idx) => (
                            <li
                              key={`${entry.id}-formula-${idx}`}
                              dangerouslySetInnerHTML={{ __html: renderMathText(item) }}
                            />
                          ))}
                        </ul>
                        <details className={styles.inlineSecret}>
                          <summary>公式解答</summary>
                          <div className={styles.inlineSecretBody}>
                            {isCurrentEntry ? (
                              <>
                                <div className={styles.field}>
                                  <label className={styles.label}>公式解答</label>
                                  <textarea
                                    className={styles.textarea}
                                    value={formulaDraft}
                                    onChange={(event) => setFormulaDraft(event.target.value)}
                                    placeholder="这里可以补充公式推导、代入过程或 LaTeX 公式。"
                                  />
                                </div>
                                {(() => {
                                  const rendered = renderFormula();
                                  if (rendered.error) {
                                    return <div className={styles.formulaError}>公式渲染失败：{rendered.error}</div>;
                                  }
                                  return <div className={styles.formulaPreview} dangerouslySetInnerHTML={{ __html: rendered.html }} />;
                                })()}
                              </>
                            ) : (
                              <>
                                <div
                                  className={styles.formulaPreviewText}
                                  dangerouslySetInnerHTML={{
                                    __html: renderMathText(entry.formulaDraft || "这道题目前没有单独公式解答。"),
                                  }}
                                />
                                <button className={styles.secondary} onClick={() => openEntryEditor(entry.id)}>
                                  编辑这题公式解答
                                </button>
                              </>
                            )}
                          </div>
                        </details>
                      </section>

                      <section ref={isCurrentEntry ? summaryRef : undefined} className={styles.cornellSection}>
                        <h3 className={styles.cornellSectionTitle}>整理</h3>
                        <div
                          className={styles.cornellBodyText}
                          dangerouslySetInnerHTML={{ __html: renderMathText(entry.result.novice_explain) }}
                        />
                        <ul className={styles.cornellFormulaList}>
                          {[...entry.result.self_questions, ...entry.result.exam_focus_prediction].map((item, idx) => (
                            <li
                              key={`${entry.id}-summary-${idx}`}
                              dangerouslySetInnerHTML={{ __html: renderMathText(item) }}
                            />
                          ))}
                        </ul>
                      </section>
                    </div>

                    {index < displayEntries.length - 1 ? <div className={styles.noteDivider} /> : null}
                  </article>
                );
                })
              )}
            </div>

            <aside className={styles.agentRail}>
              <article className={styles.agentRailCard}>
                <span className={styles.agentRailEyebrow}>{sidePanel.eyebrow}</span>
                <h3 className={styles.agentRailTitle}>{sidePanel.title}</h3>
                <p className={styles.agentRailIntro} dangerouslySetInnerHTML={{ __html: renderMathText(sidePanel.intro) }} />
                <ul className={styles.agentRailList}>
                  {sidePanel.items.map((item, idx) => (
                    <li key={`side-${idx}`} dangerouslySetInnerHTML={{ __html: renderMathText(item) }} />
                  ))}
                </ul>
                <p className={styles.agentRailFooter} dangerouslySetInnerHTML={{ __html: renderMathText(sidePanel.footer) }} />
                {showRecallPrompt && !recallDismissed ? (
                  <div className={styles.agentRailActions}>
                    <button className={styles.secondary} onClick={() => setRecallDismissed(true)}>
                      稍后再问
                    </button>
                    <button className={styles.secondary} onClick={() => void acknowledgePrompt("focus")}>
                      完成抽问
                    </button>
                  </div>
                ) : null}
              </article>

              <article className={styles.agentRailCard}>
                <span className={styles.agentRailEyebrow}>当前抓手</span>
                <h3 className={styles.agentRailTitle}>整理提醒</h3>
                <ul className={styles.agentRailList}>
                  <li>专注时长：{focusedMinutes} 分钟</li>
                  <li>当前节奏：{activeStrategyLabel}</li>
                  <li dangerouslySetInnerHTML={{ __html: renderMathText(sessionState?.next_curve_prompt || "这轮学习还没到回看节点。") }} />
                </ul>
                <p className={styles.agentRailFooter} dangerouslySetInnerHTML={{ __html: renderMathText(result.next_action) }} />
                <div className={styles.agentRailActions}>
                  <button className={styles.secondary} onClick={() => void acknowledgePrompt("curve")}>
                    完成这轮回看
                  </button>
                </div>
              </article>

              <details className={styles.agentRailCollapse}>
                <summary>练习与迁移</summary>
                <div className={styles.agentRailCollapseBody}>
                  <div className={styles.agentRailMiniBlock}>
                    <strong>小测题</strong>
                    <ul className={styles.agentRailList}>
                      {result.mini_quiz.map((item, idx) => (
                        <li key={`quiz-${idx}`} dangerouslySetInnerHTML={{ __html: renderMathText(item) }} />
                      ))}
                    </ul>
                  </div>
                  <div className={styles.agentRailMiniBlock}>
                    <strong>题型小卷</strong>
                    <ul className={styles.agentRailList}>
                      {result.practice_set.map((item, idx) => (
                        <li key={`practice-${idx}`} dangerouslySetInnerHTML={{ __html: renderMathText(item) }} />
                      ))}
                    </ul>
                  </div>
                </div>
              </details>
            </aside>
          </div>

          <div className={styles.compactArea}>
            <details className={styles.collapsePanel}>
              <summary>错题本、全量导出与补充工具</summary>
              <div className={styles.collapseInner}>
                <div className={styles.historyHeader}>
                  <h3 className={styles.panelTitle}>错题本（最近）</h3>
                  <button className={styles.secondary} onClick={fetchWrongbook}>
                    刷新
                  </button>
                </div>
                <div className={styles.historyList}>
                  {wrongbookItems.map((item) => (
                    <div key={`${item.timestamp}-${item.summary}`} className={styles.historyItem}>
                      <div className={styles.historyMeta}>
                        <span>{item.course || "课程"}</span>
                        <span className={styles.hint}>{item.timestamp}</span>
                      </div>
                      <div className={styles.historySummary}>{item.question_text}</div>
                      <div className={styles.hint}>{item.summary}</div>
                    </div>
                  ))}
                </div>
                <div className={styles.statusLine}>{wrongbookStatus}</div>
                <div className={styles.statusLine}>风险提示：{result.risk_notice}</div>
                <div className={styles.detailsBody}>
                  <button className={styles.secondary} onClick={() => exportLines("examnova-quiz.txt", "小测题", result.mini_quiz)}>
                    导出小测
                  </button>
                  <button className={styles.secondary} onClick={() => exportLines("examnova-practice-set.txt", "题型小卷", result.practice_set)}>
                    导出小卷
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbook}>
                    导出错题本
                  </button>
                  <button className={styles.secondary} onClick={exportNoteMarkdown}>
                    导出笔记 MD
                  </button>
                  <button className={styles.secondary} onClick={exportNoteWord}>
                    导出笔记 Word
                  </button>
                  <button className={styles.secondary} onClick={exportNotePdf}>
                    导出笔记 PDF
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbookMarkdown}>
                    导出错题本 MD
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbookWord}>
                    导出错题本 Word
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbookPdf}>
                    导出错题本 PDF
                  </button>
                  <button className={styles.secondary} onClick={exportNoteWordBw}>
                    导出笔记 Word（黑白）
                  </button>
                  <button className={styles.secondary} onClick={exportNotePdfBw}>
                    导出笔记 PDF（黑白）
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbookWordBw}>
                    导出错题本 Word（黑白）
                  </button>
                  <button className={styles.secondary} onClick={exportWrongbookPdfBw}>
                    导出错题本 PDF（黑白）
                  </button>
                </div>
              </div>
            </details>
          </div>
        </div>
      </section>

      <section className={styles.bottomComposer}>
        <div className={styles.bottomComposerInner}>
          <div className={styles.composerTop}>
            <input
              className={styles.composerField}
              aria-label="课程"
              value={course}
              onChange={(event) => setCourse(event.target.value)}
              placeholder="课程"
            />
            <select
              className={styles.composerField}
              aria-label="讲解模式"
              value={explanationMode}
              onChange={(event) => setExplanationMode(event.target.value)}
            >
              <option value="concise">简明</option>
              <option value="basic">从基础讲起</option>
              <option value="exam">考场优先</option>
            </select>
            <select
              className={styles.composerField}
              aria-label="复习机制"
              value={reviewMode}
              onChange={(event) => setReviewMode(event.target.value as StudyReviewMode)}
            >
              <option value="auto">自动判断</option>
              <option value="cram">冲刺模式</option>
              <option value="standard">常规模式</option>
            </select>
            <label className={`${styles.secondary} ${styles.composerAttach}`} htmlFor="ocr-file">
              识别图片
            </label>
            <input
              className={styles.hiddenInput}
              id="ocr-file"
              type="file"
              accept="image/*"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setOcrFile(file);
              }}
            />
            <button className={styles.secondary} onClick={() => scrollToEntry(activeEditorId)}>
              回到笔记
            </button>
          </div>

          <div className={styles.composerMain}>
            <textarea
              className={styles.composerTextarea}
              id="study-input"
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              placeholder="输入一道题，像微信发消息一样发给学习页。"
            />
            <div className={styles.composerStack}>
              <button className={styles.primary} onClick={() => handleAnalyze()}>
                分析题目
              </button>
              <button className={styles.secondary} onClick={handleOcr}>
                OCR 识别
              </button>
            </div>
          </div>

          <div className={styles.composerStatus}>
            <span>{status}</span>
            <span>{ocrStatus}</span>
            <span>{wrongbookStatus}</span>
          </div>
        </div>
      </section>
    </>
  );
}
