import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'

const WebSocketContext = createContext()

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [pcList, setPcList] = useState([])
  const [stats, setStats] = useState({
    total_pcs: 0,
    online_pcs: 0,
    logged_in_pcs: 0,
    locked_pcs: 0,
    offline_pcs: 0
  })

  const connect = useCallback(() => {
    try {
      const wsUrl = `ws://${window.location.hostname}:8000/ws/admin`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket 연결 성공')
        setIsConnected(true)
        setSocket(ws)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket 연결 종료')
        setIsConnected(false)
        setSocket(null)
        
        // 재연결 시도
        setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket 오류:', error)
        setIsConnected(false)
      }

    } catch (error) {
      console.error('WebSocket 연결 오류:', error)
      // 재연결 시도
      setTimeout(() => {
        connect()
      }, 3000)
    }
  }, [])

  const handleMessage = useCallback((message) => {
    switch (message.type) {
      case 'initial_pc_status':
        setPcList(message.data)
        updateStats(message.data)
        break
        
      case 'pc_connected':
        setPcList(prev => {
          const updated = prev.filter(pc => pc.pc_id !== message.data.pc_id)
          const newList = [...updated, message.data]
          updateStats(newList)
          return newList
        })
        break
        
      case 'pc_disconnected':
        setPcList(prev => {
          const updated = prev.map(pc => 
            pc.pc_id === message.data.pc_id 
              ? { ...pc, status: 'offline' }
              : pc
          )
          updateStats(updated)
          return updated
        })
        break
        
      case 'pc_status_update':
        setPcList(prev => {
          const updated = prev.map(pc => 
            pc.pc_id === message.data.pc_id 
              ? { ...pc, ...message.data }
              : pc
          )
          updateStats(updated)
          return updated
        })
        break
        
      default:
        console.log('알 수 없는 메시지 타입:', message.type)
    }
  }, [])

  const updateStats = useCallback((pcList) => {
    const total_pcs = pcList.length
    const online_pcs = pcList.filter(pc => pc.status !== 'offline').length
    const logged_in_pcs = pcList.filter(pc => pc.status === 'logged_in').length
    const locked_pcs = pcList.filter(pc => pc.status === 'locked').length
    const offline_pcs = pcList.filter(pc => pc.status === 'offline').length
    
    setStats({
      total_pcs,
      online_pcs,
      logged_in_pcs,
      locked_pcs,
      offline_pcs
    })
  }, [])

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message))
    }
  }, [socket, isConnected])

  const forceLogout = useCallback((pcId) => {
    sendMessage({
      type: 'force_logout',
      data: { pc_id: pcId }
    })
  }, [sendMessage])

  useEffect(() => {
    connect()
    
    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [connect])

  const value = {
    socket,
    isConnected,
    pcList,
    stats,
    sendMessage,
    forceLogout
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
} 