import React from 'react'
import { useWebSocket } from '../contexts/WebSocketContext'
import StatsCards from './StatsCards'
import PCGrid from './PCGrid'
import ActivityLog from './ActivityLog'

const Dashboard = () => {
  const { isConnected } = useWebSocket()

  return (
    <div className="space-y-6">
      {/* 연결 상태 알림 */}
      {!isConnected && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-4 w-4 border-2 border-warning-600 border-t-transparent rounded-full" />
            <span className="text-warning-800 font-medium">
              서버에 연결 중입니다...
            </span>
          </div>
        </div>
      )}

      {/* 통계 카드 */}
      <StatsCards />

      {/* PC 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PCGrid />
        </div>
        <div className="lg:col-span-1">
          <ActivityLog />
        </div>
      </div>
    </div>
  )
}

export default Dashboard 