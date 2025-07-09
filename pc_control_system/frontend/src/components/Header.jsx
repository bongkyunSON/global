import React, { useState } from 'react'
import { Settings, Wifi, WifiOff } from 'lucide-react'
import { useWebSocket } from '../contexts/WebSocketContext'
import SlackConfigModal from './SlackConfigModal'

const Header = () => {
  const { isConnected } = useWebSocket()
  const [showSlackModal, setShowSlackModal] = useState(false)

  return (
    <>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                PC Control System
              </h1>
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <div className="flex items-center space-x-1 text-success-600">
                    <Wifi className="h-4 w-4" />
                    <span className="text-sm font-medium">연결됨</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-1 text-error-600">
                    <WifiOff className="h-4 w-4" />
                    <span className="text-sm font-medium">연결 끊김</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowSlackModal(true)}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>Slack 설정</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <SlackConfigModal
        isOpen={showSlackModal}
        onClose={() => setShowSlackModal(false)}
      />
    </>
  )
}

export default Header 