#!/usr/bin/env node

/**
 * T106: 前端建構最佳化 - Bundle 分析工具
 * 分析打包後的檔案大小、依賴關係和載入效能
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

class BundleAnalyzer {
  constructor(distPath = './dist') {
    this.distPath = path.resolve(distPath)
    this.analysis = {
      totalSize: 0,
      files: {},
      chunks: {},
      assets: {},
      recommendations: []
    }
  }

  async analyze() {
    console.log('🔍 分析前端建構結果...\n')

    if (!fs.existsSync(this.distPath)) {
      console.error('❌ 找不到建構輸出目錄:', this.distPath)
      console.log('請先執行: npm run build')
      return
    }

    this.analyzeFiles()
    this.analyzeChunks()
    this.analyzeAssets()
    this.generateRecommendations()
    this.printReport()
  }

  analyzeFiles() {
    const walkDir = (dir, prefix = '') => {
      const files = fs.readdirSync(dir)

      files.forEach(file => {
        const filePath = path.join(dir, file)
        const relativePath = path.join(prefix, file)
        const stats = fs.statSync(filePath)

        if (stats.isDirectory()) {
          walkDir(filePath, relativePath)
        } else {
          const sizeKB = Math.round(stats.size / 1024 * 100) / 100
          this.analysis.files[relativePath] = {
            size: stats.size,
            sizeKB,
            type: path.extname(file),
            isChunk: file.includes('-') && (file.endsWith('.js') || file.endsWith('.css'))
          }
          this.analysis.totalSize += stats.size
        }
      })
    }

    walkDir(this.distPath)
  }

  analyzeChunks() {
    const jsFiles = Object.entries(this.analysis.files)
      .filter(([name, info]) => info.type === '.js' && info.isChunk)
      .sort(([,a], [,b]) => b.size - a.size)

    const cssFiles = Object.entries(this.analysis.files)
      .filter(([name, info]) => info.type === '.css' && info.isChunk)
      .sort(([,a], [,b]) => b.size - a.size)

    this.analysis.chunks = {
      javascript: jsFiles.map(([name, info]) => ({
        name,
        size: info.size,
        sizeKB: info.sizeKB,
        category: this.categorizeChunk(name)
      })),
      css: cssFiles.map(([name, info]) => ({
        name,
        size: info.size,
        sizeKB: info.sizeKB
      }))
    }
  }

  categorizeChunk(filename) {
    const name = filename.toLowerCase()

    if (name.includes('react-vendor') || name.includes('react')) return 'React 核心'
    if (name.includes('router')) return '路由'
    if (name.includes('react-query')) return '狀態管理'
    if (name.includes('icons') || name.includes('lucide')) return 'UI 圖示'
    if (name.includes('vendor')) return '第三方程式庫'
    if (name.includes('utils')) return '工具程式庫'
    if (name.includes('index')) return '應用程式主程式'

    return '其他'
  }

  analyzeAssets() {
    const assetTypes = {
      images: ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
      fonts: ['.woff', '.woff2', '.ttf', '.eot'],
      media: ['.mp4', '.webm', '.mp3', '.wav'],
      other: []
    }

    Object.entries(this.analysis.files).forEach(([name, info]) => {
      let category = 'other'

      for (const [type, extensions] of Object.entries(assetTypes)) {
        if (extensions.includes(info.type)) {
          category = type
          break
        }
      }

      if (!this.analysis.assets[category]) {
        this.analysis.assets[category] = []
      }

      this.analysis.assets[category].push({
        name,
        size: info.size,
        sizeKB: info.sizeKB
      })
    })

    // 排序每個類別的資產
    Object.keys(this.analysis.assets).forEach(category => {
      this.analysis.assets[category].sort((a, b) => b.size - a.size)
    })
  }

  generateRecommendations() {
    const totalSizeKB = Math.round(this.analysis.totalSize / 1024)
    const jsSize = this.analysis.chunks.javascript.reduce((sum, chunk) => sum + chunk.size, 0)
    const cssSize = this.analysis.chunks.css.reduce((sum, chunk) => sum + chunk.size, 0)
    const jsSizeKB = Math.round(jsSize / 1024)
    const cssSizeKB = Math.round(cssSize / 1024)

    // 大小建議
    if (totalSizeKB > 1000) {
      this.analysis.recommendations.push({
        type: 'warning',
        title: '總檔案大小過大',
        description: `目前總大小 ${totalSizeKB}KB 超過建議的 1MB`,
        suggestion: '考慮啟用 gzip/brotli 壓縮，或進一步分割程式碼'
      })
    }

    if (jsSizeKB > 500) {
      this.analysis.recommendations.push({
        type: 'warning',
        title: 'JavaScript 檔案過大',
        description: `JS 總大小 ${jsSizeKB}KB 超過建議的 500KB`,
        suggestion: '考慮延遲載入非關鍵程式碼，或使用動態匯入'
      })
    }

    // 程式碼分割建議
    const largeChunks = this.analysis.chunks.javascript.filter(chunk => chunk.sizeKB > 200)
    if (largeChunks.length > 0) {
      this.analysis.recommendations.push({
        type: 'info',
        title: '大型程式碼塊檢測',
        description: `發現 ${largeChunks.length} 個超過 200KB 的程式碼塊`,
        suggestion: '考慮進一步分割這些大型程式碼塊',
        details: largeChunks.map(chunk => `${chunk.name}: ${chunk.sizeKB}KB`)
      })
    }

    // 資產最佳化建議
    if (this.analysis.assets.images) {
      const largeImages = this.analysis.assets.images.filter(img => img.sizeKB > 100)
      if (largeImages.length > 0) {
        this.analysis.recommendations.push({
          type: 'info',
          title: '圖片最佳化機會',
          description: `發現 ${largeImages.length} 個超過 100KB 的圖片`,
          suggestion: '考慮使用 WebP 格式、圖片壓縮或延遲載入',
          details: largeImages.map(img => `${img.name}: ${img.sizeKB}KB`)
        })
      }
    }

    // 效能建議
    if (totalSizeKB < 500) {
      this.analysis.recommendations.push({
        type: 'success',
        title: '建構大小優秀',
        description: `總大小 ${totalSizeKB}KB 在建議範圍內`,
        suggestion: '繼續保持良好的最佳化實踐'
      })
    }
  }

  printReport() {
    const totalSizeKB = Math.round(this.analysis.totalSize / 1024)

    console.log('📊 前端建構分析報告')
    console.log(''.padEnd(50, '='))
    console.log(`📦 總檔案大小: ${totalSizeKB} KB`)
    console.log(`📁 檔案數量: ${Object.keys(this.analysis.files).length}`)
    console.log()

    // JavaScript 程式碼塊
    console.log('📄 JavaScript 程式碼塊:')
    this.analysis.chunks.javascript.slice(0, 10).forEach((chunk, index) => {
      const icon = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  '
      console.log(`  ${icon} ${chunk.name}`)
      console.log(`     大小: ${chunk.sizeKB} KB | 類別: ${chunk.category}`)
    })
    console.log()

    // CSS 檔案
    if (this.analysis.chunks.css.length > 0) {
      console.log('🎨 CSS 檔案:')
      this.analysis.chunks.css.forEach(chunk => {
        console.log(`     ${chunk.name}: ${chunk.sizeKB} KB`)
      })
      console.log()
    }

    // 資產檔案
    Object.entries(this.analysis.assets).forEach(([category, assets]) => {
      if (assets.length > 0) {
        const categoryNames = {
          images: '🖼️  圖片',
          fonts: '🔤 字型',
          media: '🎵 媒體',
          other: '📄 其他'
        }

        console.log(`${categoryNames[category] || category}:`)
        assets.slice(0, 5).forEach(asset => {
          console.log(`     ${asset.name}: ${asset.sizeKB} KB`)
        })

        if (assets.length > 5) {
          console.log(`     ... 還有 ${assets.length - 5} 個檔案`)
        }
        console.log()
      }
    })

    // 建議
    if (this.analysis.recommendations.length > 0) {
      console.log('💡 最佳化建議:')
      this.analysis.recommendations.forEach((rec, index) => {
        const icons = { success: '✅', warning: '⚠️', info: 'ℹ️', error: '❌' }
        console.log(`${icons[rec.type]} ${rec.title}`)
        console.log(`   ${rec.description}`)
        console.log(`   建議: ${rec.suggestion}`)

        if (rec.details) {
          console.log('   詳細資訊:')
          rec.details.slice(0, 3).forEach(detail => {
            console.log(`     • ${detail}`)
          })
          if (rec.details.length > 3) {
            console.log(`     • ... 還有 ${rec.details.length - 3} 項`)
          }
        }
        console.log()
      })
    }

    // 效能評分
    this.calculatePerformanceScore()
  }

  calculatePerformanceScore() {
    const totalSizeKB = Math.round(this.analysis.totalSize / 1024)
    const jsSize = this.analysis.chunks.javascript.reduce((sum, chunk) => sum + chunk.size, 0)
    const jsSizeKB = Math.round(jsSize / 1024)

    let score = 100

    // 大小評分
    if (totalSizeKB > 2000) score -= 30
    else if (totalSizeKB > 1000) score -= 20
    else if (totalSizeKB > 500) score -= 10

    // JS 大小評分
    if (jsSizeKB > 800) score -= 20
    else if (jsSizeKB > 500) score -= 15
    else if (jsSizeKB > 300) score -= 10

    // 程式碼分割評分
    const chunkCount = this.analysis.chunks.javascript.length
    if (chunkCount < 3) score -= 15
    else if (chunkCount < 5) score -= 5

    // 大型檔案懲罰
    const largeFiles = Object.values(this.analysis.files).filter(file => file.sizeKB > 300)
    score -= largeFiles.length * 10

    score = Math.max(0, score)

    let grade = 'F'
    let color = '🔴'

    if (score >= 90) { grade = 'A+'; color = '🟢' }
    else if (score >= 80) { grade = 'A'; color = '🟢' }
    else if (score >= 70) { grade = 'B'; color = '🟡' }
    else if (score >= 60) { grade = 'C'; color = '🟠' }
    else if (score >= 50) { grade = 'D'; color = '🔴' }

    console.log('🏆 效能評分:')
    console.log(`   分數: ${score}/100`)
    console.log(`   等級: ${grade} ${color}`)

    if (score >= 80) {
      console.log('   🎉 建構最佳化表現優秀！')
    } else if (score >= 60) {
      console.log('   👍 建構最佳化還不錯，但有改善空間')
    } else {
      console.log('   ⚠️  建構需要進一步最佳化')
    }
  }

  generateJsonReport() {
    const reportData = {
      timestamp: new Date().toISOString(),
      summary: {
        totalSize: this.analysis.totalSize,
        totalSizeKB: Math.round(this.analysis.totalSize / 1024),
        fileCount: Object.keys(this.analysis.files).length,
        chunkCount: this.analysis.chunks.javascript.length
      },
      chunks: this.analysis.chunks,
      assets: this.analysis.assets,
      recommendations: this.analysis.recommendations
    }

    const reportPath = path.join(this.distPath, 'bundle-analysis.json')
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2))
    console.log(`📋 詳細報告已儲存至: ${reportPath}`)
  }
}

// 檢查是否有建構檔案
const checkBuildExists = () => {
  const distPath = path.resolve('./dist')
  if (!fs.existsSync(distPath)) {
    console.log('🔨 未找到建構輸出，正在執行建構...')
    try {
      execSync('npm run build', { stdio: 'inherit' })
    } catch (error) {
      console.error('❌ 建構失敗:', error.message)
      process.exit(1)
    }
  }
}

// 主程式
async function main() {
  const args = process.argv.slice(2)
  const shouldBuild = args.includes('--build')
  const shouldGenerateReport = args.includes('--report')

  if (shouldBuild) {
    checkBuildExists()
  }

  const analyzer = new BundleAnalyzer()
  await analyzer.analyze()

  if (shouldGenerateReport) {
    analyzer.generateJsonReport()
  }
}

if (require.main === module) {
  main().catch(console.error)
}

module.exports = { BundleAnalyzer }