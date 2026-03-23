import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI 内容分析工具 - 抖音/小红书数据化运营助手',
  description: '输入抖音/小红书链接，AI自动分析8个维度数据，提供专业优化建议，助力内容创作和运营增长',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
