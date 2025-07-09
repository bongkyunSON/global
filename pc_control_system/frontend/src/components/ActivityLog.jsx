import React, { useState, useEffect } from 'react'
import { Activity, LogIn, LogOut, Monitor, Clock } from 'lucide-react'
import { useWebSocket } from '../contexts/WebSocketContext'

const ActivityLog = () => {
  const { pcList } = useWebSocket()
  const [activities, setActivities] = useState([])

  // PC 상태 변경을 감지하여 활동 로그 생성
  useEffect(() => {
    const newActivities = []
    
    pcList.forEach(pc => {
      if (pc.status === 'logged_in' && pc.username && pc.login_time) {
        newActivities.push({
          id: `${pc.pc_id}-login-${pc.login_time}`,
          type: 'login',
          pcId: pc.pc_id,
          username: pc.username,
          organization: pc.organization,
          timestamp: new Date(pc.login_time),
          message: `${pc.username}님이 PC-${pc.pc_id}에 로그인했습니다.`
        })
      }
    })
    
    // 시간 순으로 정렬 (최신순)
    newActivities.sort((a, b) => b.timestamp - a.timestamp)
    
    setActivities(newActivities.slice(0, 10)) // 최근 10개만 표시
  }, [pcList])

  const getActivityIcon = (type) => {
    switch (type) {
      case 'login':
        return <LogIn className="h-4 w-4 text-success-600" />
      case 'logout':
        return <LogOut className="h-4 w-4 text-warning-600" />
      case 'connect':
        return <Monitor className="h-4 w-4 text-primary-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    
    const now = new Date()
    const diff = now - timestamp
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (days > 0) {
      return `${days}일 전`
    } else if (hours > 0) {
      return `${hours}시간 전`
    } else if (minutes > 0) {
      return `${minutes}분 전`
    } else {
      return '방금 전'
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-lg font-semibold">활동 로그</h2>
        <p className="text-sm text-gray-600">
          최근 로그인 활동
        </p>
      </div>
      
      <div className="card-body">
        {activities.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>최근 활동이 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 mt-0.5">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    {activity.message}
                  </p>
                  {activity.organization && (
                    <p className="text-xs text-gray-500 mt-1">
                      소속: {activity.organization}
                    </p>
                  )}
                  <div className="flex items-center space-x-2 mt-2 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    <span>{formatTime(activity.timestamp)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ActivityLog 