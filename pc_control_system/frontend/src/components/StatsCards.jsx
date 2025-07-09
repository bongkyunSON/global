import React from 'react'
import { Monitor, CheckCircle, Lock, WifiOff } from 'lucide-react'
import { useWebSocket } from '../contexts/WebSocketContext'

const StatsCards = () => {
  const { stats } = useWebSocket()

  const statItems = [
    {
      title: '전체 PC',
      value: stats.total_pcs,
      icon: Monitor,
      color: 'bg-primary-50 text-primary-600',
      bgColor: 'bg-primary-500',
    },
    {
      title: '로그인 중',
      value: stats.logged_in_pcs,
      icon: CheckCircle,
      color: 'bg-success-50 text-success-600',
      bgColor: 'bg-success-500',
    },
    {
      title: '잠금 상태',
      value: stats.locked_pcs,
      icon: Lock,
      color: 'bg-warning-50 text-warning-600',
      bgColor: 'bg-warning-500',
    },
    {
      title: '오프라인',
      value: stats.offline_pcs,
      icon: WifiOff,
      color: 'bg-gray-50 text-gray-600',
      bgColor: 'bg-gray-500',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <div key={item.title} className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{item.title}</p>
                <p className="text-2xl font-bold text-gray-900">{item.value}</p>
              </div>
              <div className={`p-3 rounded-full ${item.color}`}>
                <item.icon className="h-6 w-6" />
              </div>
            </div>
            
            {/* 진행률 바 */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>사용률</span>
                <span>
                  {stats.total_pcs > 0 
                    ? Math.round((item.value / stats.total_pcs) * 100)
                    : 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${item.bgColor} transition-all duration-300`}
                  style={{
                    width: `${stats.total_pcs > 0 
                      ? (item.value / stats.total_pcs) * 100 
                      : 0}%`
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StatsCards 