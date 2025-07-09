import React from 'react'
import { useWebSocket } from '../contexts/WebSocketContext'
import PCCard from './PCCard'

const PCGrid = () => {
  const { pcList } = useWebSocket()

  // PC ID 순으로 정렬
  const sortedPcList = [...pcList].sort((a, b) => a.pc_id.localeCompare(b.pc_id))

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-lg font-semibold">PC 현황</h2>
        <p className="text-sm text-gray-600">
          총 {pcList.length}대의 PC가 관리되고 있습니다.
        </p>
      </div>
      
      <div className="card-body">
        {sortedPcList.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>연결된 PC가 없습니다.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedPcList.map((pc) => (
              <PCCard key={pc.pc_id} pc={pc} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default PCGrid 