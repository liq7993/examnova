import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ExamNova",
  description: "面向中国大学生的桌面学习 Agent。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
