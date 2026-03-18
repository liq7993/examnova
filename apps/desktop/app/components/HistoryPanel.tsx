"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";

import styles from "../page.module.css";

type Props = {
  backendUrl: string;
  compact?: boolean;
};

type HistoryItem = {
  timestamp: string;
  task: "study" | "thinking" | "companion";
  summary: string;
};

const taskLabels: Record<HistoryItem["task"], string> = {
  study: "学习",
  thinking: "写作与复盘",
  companion: "旧版陪伴",
};

async function loadHistory(
  backendUrl: string,
  setItems: Dispatch<SetStateAction<HistoryItem[]>>,
  setStatus: Dispatch<SetStateAction<string>>,
) {
  setStatus("正在加载记录...");
  try {
    const response = await fetch(`${backendUrl}/api/history/recent?limit=6`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = (await response.json()) as { items: HistoryItem[] };
    setItems(payload.items);
    setStatus(payload.items.length ? "最近记录已更新。" : "暂无记录。");
  } catch (error) {
    const message = error instanceof Error ? error.message : "未知错误";
    setStatus(`读取失败：${message}`);
  }
}

export function HistoryPanel({ backendUrl, compact = false }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [status, setStatus] = useState("正在加载记录...");

  async function fetchHistory() {
    await loadHistory(backendUrl, setItems, setStatus);
  }

  function downloadText(filename: string, content: string) {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function exportHistory() {
    setStatus("正在导出记录...");
    try {
      const response = await fetch(`${backendUrl}/api/history/export`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = (await response.json()) as { items: HistoryItem[] };
      const content = payload.items
        .map((item) => `${item.timestamp} [${taskLabels[item.task]}] ${item.summary}`)
        .join("\n");
      downloadText("examnova-history.txt", content || "暂无记录。");
      setStatus("导出完成。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`导出失败：${message}`);
    }
  }

  async function clearHistory() {
    setStatus("正在清空记录...");
    try {
      const response = await fetch(`${backendUrl}/api/history/clear`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      setItems([]);
      setStatus("记录已清空。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "未知错误";
      setStatus(`清空失败：${message}`);
    }
  }

  useEffect(() => {
    void loadHistory(backendUrl, setItems, setStatus);
  }, [backendUrl]);

  return (
    <section className={compact ? `${styles.panel} ${styles.historyCompact}` : styles.panel}>
      <div className={styles.historyHeader}>
        <h2 className={styles.panelTitle}>最近记录</h2>
        <div className={styles.historyActions}>
          <button className={styles.secondary} onClick={fetchHistory}>
            刷新
          </button>
          <button className={styles.secondary} onClick={exportHistory}>
            导出
          </button>
          <button className={styles.secondary} onClick={clearHistory}>
            清空
          </button>
        </div>
      </div>
      <div className={styles.historyList}>
        {items.map((item, index) => (
          <div key={`${item.timestamp}-${index}`} className={styles.historyItem}>
            <div className={styles.historyMeta}>
              <span>{taskLabels[item.task]}</span>
              <span className={styles.hint}>{item.timestamp}</span>
            </div>
            <div className={styles.historySummary}>{item.summary}</div>
          </div>
        ))}
      </div>
      <div className={styles.statusLine}>{status}</div>
    </section>
  );
}
