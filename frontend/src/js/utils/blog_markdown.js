/**
 * 把 markdown 转成 HTML，供博客正文展示。
 * 轻量实现：标题、列表、引用、代码块、粗体、斜体、链接、图片、分隔线。
 */

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function inline(text) {
  let out = escapeHtml(text)
  // 代码
  out = out.replace(/`([^`]+)`/g, '<code class="px-1 rounded bg-base-200">$1</code>')
  // 图片（放在链接之前处理）
  out = out.replace(/!\[([^\]]*)]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="max-w-full rounded-lg my-2" />')
  // 链接
  out = out.replace(/\[([^\]]+)]\(([^)]+)\)/g, '<a href="$2" class="link link-primary">$1</a>')
  // 粗体
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 斜体
  out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  return out
}

export function renderMarkdown(markdown) {
  if (!markdown) return ''

  const lines = String(markdown).split('\n')
  const html = []
  let inCode = false
  let codeBuffer = []
  let inList = false

  const closeList = () => {
    if (inList) {
      html.push('</ul>')
      inList = false
    }
  }

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '')

    // 代码块
    if (line.trim().startsWith('```')) {
      if (inCode) {
        html.push(`<pre class="bg-base-200 p-4 rounded-lg overflow-x-auto my-4"><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>`)
        codeBuffer = []
        inCode = false
      } else {
        closeList()
        inCode = true
      }
      continue
    }

    if (inCode) {
      codeBuffer.push(raw)
      continue
    }

    // 空行
    if (!line.trim()) {
      closeList()
      continue
    }

    // 分隔线
    if (/^(-{3,}|\*{3,})$/.test(line.trim())) {
      closeList()
      html.push('<hr class="my-4" />')
      continue
    }

    // 标题
    const heading = line.match(/^(#{1,6})\s+(.*)$/)
    if (heading) {
      closeList()
      const level = heading[1].length
      html.push(`<h${level} class="font-bold mt-4 mb-2">${inline(heading[2])}</h${level}>`)
      continue
    }

    // 引用
    if (line.startsWith('>')) {
      closeList()
      html.push(`<blockquote class="border-l-4 border-base-300 pl-4 py-1 my-2 opacity-80">${inline(line.slice(1).trim())}</blockquote>`)
      continue
    }

    // 无序列表
    const listItem = line.match(/^\s*[-*+]\s+(.*)$/)
    if (listItem) {
      if (!inList) {
        html.push('<ul class="list-disc list-inside my-2 space-y-1">')
        inList = true
      }
      html.push(`<li>${inline(listItem[1])}</li>`)
      continue
    }

    // 普通段落
    closeList()
    html.push(`<p class="my-2 leading-relaxed">${inline(line)}</p>`)
  }

  if (inCode && codeBuffer.length) {
    html.push(`<pre class="bg-base-200 p-4 rounded-lg overflow-x-auto my-4"><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>`)
  }
  closeList()

  return html.join('')
}

export default renderMarkdown