import React from 'react'
import { Monitor, User, Building, Clock, LogOut, Wifi } from 'lucide-react'
import { useWebSocket } from '../contexts/WebSocketContext'
import { formatDistanceToNow } from 'date-fns'

const PCCard = ({ pc }) => {
  const { forceLogout } = useWebSocket()

  const getStatusBadge = (status) => {
    switch (status) {
      case 'logged_in':
        return (
          <span className="status-badge status-badge-logged-in">
            로그인 중
          </span>
        )
      case 'locked':
        return (
          <span className="status-badge status-badge-locked">
            잠금 상태
          </span>
        )
      case 'offline':
        return (
          <span className="status-badge status-badge-offline">
            오프라인
          </span>
        )
      default:
        return null
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'logged_in':
        return 'text-success-600'
      case 'locked':
        return 'text-warning-600'
      case 'offline':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const formatTime = (timeString) => {
    if (!timeString) return null
    try {
      const date = new Date(timeString)
      return formatDistanceToNow(date, { addSuffix: true })
    } catch (error) {
      return null
    }
  }

  const handleForceLogout = () => {
    if (window.confirm(`PC-${pc.pc_id}의 사용자를 강제 로그아웃하시겠습니까?`)) {
      forceLogout(pc.pc_id)
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* PC 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Monitor className={`h-5 w-5 ${getStatusColor(pc.status)}`} />
          <span className="font-medium text-gray-900">PC-{pc.pc_id}</span>
        </div>
        {getStatusBadge(pc.status)}
      </div>

      {/* 사용자 정보 */}
      {pc.status === 'logged_in' && pc.username && (
        <div className="space-y-2 mb-3">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <User className="h-4 w-4" />
            <span>{pc.username}</span>
          </div>
          {pc.organization && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Building className="h-4 w-4" />
              <span>{pc.organization}</span>
            </div>
          )}
          {pc.login_time && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>{formatTime(pc.login_time)}</span>
            </div>
          )}
        </div>
      )}

      {/* IP 주소 및 마지막 접속 */}
      <div className="space-y-1 text-xs text-gray-500 mb-3">
        {pc.ip_address && (
          <div className="flex items-center space-x-2">
            <Wifi className="h-3 w-3" />
            <span>IP: {pc.ip_address}</span>
          </div>
        )}
        {pc.last_heartbeat && (
          <div className="flex items-center space-x-2">
            <Clock className="h-3 w-3" />
            <span>마지막 접속: {formatTime(pc.last_heartbeat)}</span>
          </div>
        )}
      </div>

      {/* 액션 버튼 */}
      {pc.status === 'logged_in' && (
        <div className="flex space-x-2">
          <button
            onClick={handleForceLogout}
            className="flex-1 btn btn-error text-sm py-1.5 flex items-center justify-center space-x-1"
          >
            <LogOut className="h-4 w-4" />
            <span>강제 로그아웃</span>
          </button>
        </div>
      )}

      {/* 오프라인 상태 표시 */}
      {pc.status === 'offline' && (
        <div className="text-center text-gray-500 text-sm py-2">
          PC가 오프라인 상태입니다.
        </div>
      )}
    </div>
  )
}

export default PCCard 