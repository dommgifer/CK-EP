/**
 * 錯誤警示組件
 * 用於顯示錯誤訊息和重試選項
 */
import React from 'react'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

interface ErrorAlertProps {
  title: string
  message: string
  onRetry?: () => void
  className?: string
}

export default function ErrorAlert({ title, message, onRetry, className = '' }: ErrorAlertProps) {
  return (
    <div className={`rounded-md bg-red-50 p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-red-50"
              >
                <ArrowPathIcon className="mr-1 h-4 w-4" />
                重試
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}