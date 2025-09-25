/**
 * 首頁
 * 基於設計原型的現代化首頁介面 - 暗色主題版本
 */
import React, { useState } from 'react'
import { Clock, BookOpen, Target } from 'lucide-react'
import { mockQuestions, examConfig } from '../data/questions'
import { Card } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { ExamSetupDialog } from '../components/ExamSetupDialog'
import heroImage from '../assets/k8s-hero.jpg'

const HomePage = () => {
  const [examStarted, setExamStarted] = useState(false)
  const [showExamSetupDialog, setShowExamSetupDialog] = useState(false)

  const startDeployment = () => {
    setShowExamSetupDialog(true)
  }

  const handleStartDeployment = () => {
    setShowExamSetupDialog(false)
    // 這裡可以添加部署邏輯
  }

  if (examStarted) {
    return <div>考試進行中...</div>
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative h-screen flex items-center justify-center">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${heroImage})` }}
        >
          <div className="absolute inset-0 bg-background/80" />
        </div>

        <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
          <div className="mb-8">
            <h1 className="text-5xl font-bold text-foreground mb-4">
              Kubernetes 認證考試模擬器
            </h1>
            <p className="text-xl text-muted-foreground mb-8">
              體驗真實的 CKA/CKAD 考試環境，提升您的 Kubernetes 技能
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="p-6 bg-card/90 backdrop-blur border-border">
              <div className="flex items-center gap-3 mb-3">
                <Clock className="h-8 w-8 text-primary" />
                <h3 className="text-lg font-semibold text-card-foreground">真實計時</h3>
              </div>
              <p className="text-muted-foreground text-sm">
                {examConfig.timeLimit} 分鐘的考試時間，模擬真實考試節奏
              </p>
            </Card>

            <Card className="p-6 bg-card/90 backdrop-blur border-border">
              <div className="flex items-center gap-3 mb-3">
                <BookOpen className="h-8 w-8 text-primary" />
                <h3 className="text-lg font-semibold text-card-foreground">實務題目</h3>
              </div>
              <p className="text-muted-foreground text-sm">
                {examConfig.totalQuestions} 道精心設計的 Kubernetes 實務題目
              </p>
            </Card>

            <Card className="p-6 bg-card/90 backdrop-blur border-border">
              <div className="flex items-center gap-3 mb-3">
                <Target className="h-8 w-8 text-primary" />
                <h3 className="text-lg font-semibold text-card-foreground">專業評分</h3>
              </div>
              <p className="text-muted-foreground text-sm">
                總分 {examConfig.maxPoints} 分，通過分數 {examConfig.passingScore} 分
              </p>
            </Card>
          </div>

          <div className="space-y-4">
            <div className="flex justify-center">
              <Button
                onClick={startDeployment}
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 text-lg"
              >
                考試設定
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Exam Setup Dialog */}
      <ExamSetupDialog
        open={showExamSetupDialog}
        onOpenChange={setShowExamSetupDialog}
        onStartDeployment={handleStartDeployment}
      />
    </div>
  )
}

export default HomePage