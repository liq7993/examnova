"use client";

import { useState } from "react";

import styles from "../page.module.css";
import type { ThinkingResponse } from "../types";

type Props = {
  backendUrl: string;
  initialData: ThinkingResponse;
};

function exportLines(filename: string, title: string, items: string[]) {
  const content = [title, ...items.map((item) => `- ${item}`), ""].join("\n");
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ThinkingPanel({ backendUrl, initialData }: Props) {
  const [idea, setIdea] = useState("今天复习结束后，怎样写一段不自我否定的学习总结？");
  const [mode, setMode] = useState("essay");
  const [rewriteStyle, setRewriteStyle] = useState("");
  const [result, setResult] = useState<ThinkingResponse>(initialData);
  const [status, setStatus] = useState("等待扩展。");
  const [notes, setNotes] = useState("");

  async function handleExpand() {
    setStatus("正在整理内容...");

    try {
      const response = await fetch(`${backendUrl}/api/agent/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: "thinking",
          payload: {
            idea,
            mode,
            rewrite_style: rewriteStyle || undefined,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = (await response.json()) as { result: ThinkingResponse };
      setResult(payload.result);
      setStatus("写作与复盘结果已更新。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`请求失败：${message}`);
    }
  }

  function exportDraft() {
    const content = [
      `标题：${result.title}`,
      `模式：${result.mode}`,
      `语气：${result.tone_tags.join("、")}`,
      `一句话总结：${result.summary}`,
      "",
      "信心提示：",
      result.confidence_note,
      "",
      "要点：",
      ...result.key_points.map((item) => `- ${item}`),
      "",
      "复盘桥接：",
      ...result.review_bridge.map((item) => `- ${item}`),
      "",
      "行动清单：",
      ...result.action_list.map((item) => `- ${item}`),
      "",
      "大纲：",
      ...result.outline.map((item, index) => `${index + 1}. ${item}`),
      "",
      "正文：",
      result.content,
      "",
      "改写方向：",
      ...result.rewrite_options.map((item) => `- ${item}`),
      "",
      "反思问题：",
      result.reflection_prompt,
      "",
      "个人备注：",
      notes || "（空）",
      "",
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = result.export_title || "examnova-writing.txt";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>写作与复盘</h2>
        <div className={styles.formGrid}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="thinking-mode">
              模式
            </label>
            <select
              className={styles.select}
              id="thinking-mode"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              <option value="essay">随笔</option>
              <option value="review">复盘</option>
              <option value="outline">大纲</option>
              <option value="reflection">反思</option>
              <option value="script">脚本</option>
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="thinking-style">
              改写风格
            </label>
            <input
              className={styles.input}
              id="thinking-style"
              value={rewriteStyle}
              onChange={(event) => setRewriteStyle(event.target.value)}
              placeholder="例如：更克制 / 更直接 / 更像复盘记录"
            />
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="thinking-input">
            原始内容
          </label>
          <textarea
            className={styles.textarea}
            id="thinking-input"
            value={idea}
            onChange={(event) => setIdea(event.target.value)}
          />
        </div>

        <div className={styles.actions}>
          <button className={styles.primary} onClick={handleExpand}>
            整理内容
          </button>
          <button className={styles.secondary} onClick={exportDraft}>
            导出草稿
          </button>
          <button
            className={styles.secondary}
            onClick={() => {
              setRewriteStyle(result.rewrite_options[0] || "更克制");
              void handleExpand();
            }}
          >
            一键改写
          </button>
        </div>

        <div className={styles.statusLine}>{status}</div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>{result.title}</h2>
        <p className={styles.cardText}>{result.content}</p>
        <div className={styles.resultGrid}>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>大纲</h3>
            <ul className={styles.list}>
              {result.outline.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>要点</h3>
            <ul className={styles.list}>
              {result.key_points.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>语气标签</h3>
            <div className={styles.chipList}>
              {result.tone_tags.map((item) => (
                <span key={item} className={styles.chip}>
                  {item}
                </span>
              ))}
            </div>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>一句话总结</h3>
            <p className={styles.cardText}>{result.summary}</p>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>信心提示</h3>
            <p className={styles.cardText}>{result.confidence_note}</p>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>行动清单</h3>
            <ul className={styles.list}>
              {result.action_list.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>复盘桥接</h3>
            <ul className={styles.list}>
              {result.review_bridge.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>反思问题</h3>
            <p className={styles.cardText}>{result.reflection_prompt}</p>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>改写选项</h3>
            <ul className={styles.list}>
              {result.rewrite_options.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        </div>
        <div className={styles.actions}>
          <button
            className={styles.secondary}
            onClick={() => exportLines(result.export_title, "大纲", result.outline)}
          >
            导出大纲
          </button>
          <button
            className={styles.secondary}
            onClick={() => exportLines(result.export_title, "正文", [result.content])}
          >
            导出正文
          </button>
        </div>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="thinking-notes">
            个人备注
          </label>
          <textarea
            className={styles.textarea}
            id="thinking-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="记下你明天想继续写、继续复习或继续查漏的地方。"
          />
        </div>
      </section>
    </>
  );
}
