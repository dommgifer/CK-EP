/**
 * 首頁
 * 基於設計原型的現代化首頁介面 - 暗色主題版本
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, BookOpen, Target } from 'lucide-react'
import { mockQuestions, examConfig } from '../data/questions'
import { Card } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { ExamSetupDialog } from '../components/ExamSetupDialog'
import { DeploymentDialog } from '../components/DeploymentDialog'
import { SessionRecoveryDialog } from '../components/SessionRecoveryDialog'
import { apiClient } from '../services/api'
// import heroImage from '../assets/k8s-hero.jpg'

interface ActiveSession {
  id: string;
  question_set_id: string;
  status: string;
  created_at: string;
  start_time: string | null;
}

const HomePage = () => {
  const navigate = useNavigate()
  const [showExamSetupDialog, setShowExamSetupDialog] = useState(false)
  const [showDeploymentDialog, setShowDeploymentDialog] = useState(false)
  const [showSessionRecoveryDialog, setShowSessionRecoveryDialog] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [detectedSession, setDetectedSession] = useState<ActiveSession | null>(null)
  const [deploymentParams, setDeploymentParams] = useState<{
    examType: string;
    examSet: string;
    vmConfigId: string;
  } | undefined>(undefined)

  // 頁面載入時檢查是否有活動的考試會話
  useEffect(() => {
    const checkActiveSession = async () => {
      try {
        const response = await apiClient.get<ActiveSession[]>('/exam-sessions?status=in_progress')

        if (response.data.length > 0) {
          // 取第一個活動的 session
          const activeSession = response.data[0]
          setDetectedSession(activeSession)
          setShowSessionRecoveryDialog(true)
        }
      } catch (error) {
        console.error('檢查活動會話失敗:', error)
        // 靜默失敗，不影響使用者體驗
      }
    }

    checkActiveSession()
  }, []) // 只在頁面載入時執行一次

  const startDeployment = () => {
    setShowExamSetupDialog(true)
  }

  const handleStartDeployment = (params: {
    examType: string;
    examSet: string;
    vmConfigId: string;
  }) => {
    setDeploymentParams(params)
    setShowExamSetupDialog(false)
    setShowDeploymentDialog(true)
  }

  const handleDeploymentComplete = (sessionId: string) => {
    setShowDeploymentDialog(false)
    setCurrentSessionId(sessionId)

    // 導航到考試頁面
    navigate(`/exam/${sessionId}`)
  }

  // 恢復考試
  const handleResumeExam = () => {
    if (detectedSession) {
      setShowSessionRecoveryDialog(false)
      navigate(`/exam/${detectedSession.id}`)
    }
  }

  // 停止並開始新考試
  const handleStopAndStartNew = async () => {
    if (detectedSession) {
      try {
        // 更新 session 狀態為 cancelled
        await apiClient.patch(`/exam-sessions/${detectedSession.id}`, {
          status: 'cancelled'
        })

        setShowSessionRecoveryDialog(false)
        setDetectedSession(null)

        // 可選：顯示考試設定對話框讓使用者開始新考試
        // setShowExamSetupDialog(true)
      } catch (error) {
        console.error('停止會話失敗:', error)
        // 可以顯示錯誤訊息
      }
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative h-screen flex items-center justify-center">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat bg-gray-800"
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

      {/* Session Recovery Dialog */}
      <SessionRecoveryDialog
        open={showSessionRecoveryDialog}
        onOpenChange={setShowSessionRecoveryDialog}
        sessionData={detectedSession}
        onResumeExam={handleResumeExam}
        onStopAndStartNew={handleStopAndStartNew}
      />

      {/* Exam Setup Dialog */}
      <ExamSetupDialog
        open={showExamSetupDialog}
        onOpenChange={setShowExamSetupDialog}
        onStartDeployment={handleStartDeployment}
      />

      {/* Deployment Dialog */}
      <DeploymentDialog
        open={showDeploymentDialog}
        onOpenChange={setShowDeploymentDialog}
        onDeploymentComplete={handleDeploymentComplete}
        deploymentParams={deploymentParams}
      />
    </div>
  )
}

export default HomePage