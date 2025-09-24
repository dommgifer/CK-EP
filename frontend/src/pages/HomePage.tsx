/**
 * 首頁
 * 系統概覽和快速操作入口
 */
import React from 'react'
import { Link } from 'react-router-dom'
import {
  ServerIcon,
  DocumentTextIcon,
  AcademicCapIcon,
  PlayIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

export default function HomePage() {
  const features = [
    {
      name: 'VM 配置管理',
      description: '管理您的 Kubernetes 叢集配置，設定 SSH 連線',
      icon: ServerIcon,
      href: '/vm-configs',
      color: 'blue'
    },
    {
      name: '題組瀏覽',
      description: '探索 CKA、CKAD、CKS 考試題組',
      icon: DocumentTextIcon,
      href: '/question-sets',
      color: 'green'
    },
    {
      name: '開始考試',
      description: '建立新的考試會話，開始練習',
      icon: AcademicCapIcon,
      href: '/create-exam',
      color: 'purple'
    }
  ]

  const stats = [
    { name: '支援認證類型', value: '3', description: 'CKA、CKAD、CKS' },
    { name: '平均考試時長', value: '120', description: '分鐘' },
    { name: '題目類型', value: '實作題', description: 'Hands-on 練習' },
    { name: '環境準備', value: '<5', description: '分鐘內完成' }
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          Kubernetes 考試模擬器
        </h1>
        <p className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
          提供真實的 Kubernetes 認證考試環境，支援 CKA、CKAD、CKS 三種認證。
          自動化環境配置，即時評分，助您順利通過認證考試。
        </p>
        <div className="mt-10 flex items-center justify-center gap-x-6">
          <Link
            to="/create-exam"
            className="inline-flex items-center rounded-md bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            <PlayIcon className="h-5 w-5 mr-2" />
            開始考試
          </Link>
          <Link
            to="/question-sets"
            className="text-sm font-semibold leading-6 text-gray-900 hover:text-gray-700"
          >
            瀏覽題組 <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-white py-12 sm:py-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-x-8 gap-y-16 text-center lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="mx-auto flex max-w-xs flex-col gap-y-4">
                <dt className="text-base leading-7 text-gray-600">{stat.name}</dt>
                <dd className="order-first text-3xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
                  {stat.value}
                </dd>
                <p className="text-sm text-gray-500">{stat.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="bg-gray-50 py-12 sm:py-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              功能特色
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              完整的考試環境配置和管理功能
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <feature.icon
                      className={`h-5 w-5 flex-none text-${feature.color}-600`}
                      aria-hidden="true"
                    />
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                    <p className="mt-6">
                      <Link
                        to={feature.href}
                        className={`text-sm font-semibold leading-6 text-${feature.color}-600 hover:text-${feature.color}-500`}
                      >
                        立即使用 <span aria-hidden="true">→</span>
                      </Link>
                    </p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="bg-white">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              系統架構
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              基於容器化技術的現代考試環境
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 lg:mx-0 lg:max-w-none lg:grid-cols-2">
            <div className="bg-gray-50 rounded-2xl p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">技術特點</h3>
              <ul className="space-y-3 text-gray-600">
                <li className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-green-500 mr-3" />
                  自動化 Kubernetes 環境部署
                </li>
                <li className="flex items-center">
                  <ServerIcon className="h-5 w-5 text-blue-500 mr-3" />
                  VNC 遠端桌面存取
                </li>
                <li className="flex items-center">
                  <ClockIcon className="h-5 w-5 text-purple-500 mr-3" />
                  即時自動化評分
                </li>
                <li className="flex items-center">
                  <DocumentTextIcon className="h-5 w-5 text-orange-500 mr-3" />
                  檔案系統題庫管理
                </li>
              </ul>
            </div>

            <div className="bg-gray-50 rounded-2xl p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">支援認證</h3>
              <div className="space-y-4">
                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-semibold text-gray-900">CKA (Certified Kubernetes Administrator)</h4>
                  <p className="text-sm text-gray-600">Kubernetes 管理員認證</p>
                </div>
                <div className="border-l-4 border-purple-500 pl-4">
                  <h4 className="font-semibold text-gray-900">CKAD (Certified Kubernetes Application Developer)</h4>
                  <p className="text-sm text-gray-600">Kubernetes 應用開發者認證</p>
                </div>
                <div className="border-l-4 border-orange-500 pl-4">
                  <h4 className="font-semibold text-gray-900">CKS (Certified Kubernetes Security Specialist)</h4>
                  <p className="text-sm text-gray-600">Kubernetes 安全專家認證</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}