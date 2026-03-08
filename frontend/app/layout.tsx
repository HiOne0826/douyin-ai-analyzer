import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI社交媒体内容分析系统',
  description: '智能分析抖音/小红书内容，提供专业的优化建议和对标分析',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-white">
        <header className="border-b-4 border-black py-6">
          <div className="container mx-auto px-4">
            <h1 className="text-4xl font-bold">
              <span className="bg-black text-white px-2">AI</span> 内容分析
            </h1>
            <p className="mt-2 text-lg">抖音/小红书智能分析工具</p>
          </div>
        </header>
        <main className="container mx-auto px-4 py-12">
          {children}
        </main>
        <footer className="border-t-4 border-black py-8 mt-12">
          <div className="container mx-auto px-4 text-center">
            <p>© 2024 AI内容分析系统 | 极简主义·新野兽派</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
