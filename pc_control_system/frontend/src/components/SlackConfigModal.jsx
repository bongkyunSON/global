import React, { useState } from 'react'
import { X, Send } from 'lucide-react'
import axios from 'axios'

const SlackConfigModal = ({ isOpen, onClose }) => {
  const [webhookUrl, setWebhookUrl] = useState('')
  const [channel, setChannel] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    setMessage('')

    try {
      const response = await axios.post('/api/slack/config', {
        webhook_url: webhookUrl,
        channel: channel
      })

      if (response.data.success) {
        setMessage('Slack 설정이 성공적으로 저장되었습니다!')
        setTimeout(() => {
          onClose()
          setWebhookUrl('')
          setChannel('')
          setMessage('')
        }, 2000)
      } else {
        setMessage(response.data.message || 'Slack 설정 저장에 실패했습니다.')
      }
    } catch (error) {
      console.error('Slack 설정 오류:', error)
      setMessage('Slack 설정 중 오류가 발생했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold">Slack 설정</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              웹훅 URL *
            </label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="https://hooks.slack.com/services/..."
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Slack 워크스페이스에서 웹훅 URL을 생성하여 입력하세요.
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              채널 (선택사항)
            </label>
            <input
              type="text"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="#general"
            />
            <p className="mt-1 text-xs text-gray-500">
              비워두면 웹훅 기본 채널로 전송됩니다.
            </p>
          </div>
          
          {message && (
            <div className={`p-3 rounded-md text-sm ${
              message.includes('성공') 
                ? 'bg-success-50 text-success-800' 
                : 'bg-error-50 text-error-800'
            }`}>
              {message}
            </div>
          )}
          
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn btn-secondary"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !webhookUrl}
              className="flex-1 btn btn-primary flex items-center justify-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  <span>저장 중...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>저장</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SlackConfigModal 