import { io } from 'socket.io-client'

class WebSocketService {
  constructor() {
    this.socket = null
    this.connected = false
    this.listeners = new Map()
  }

  connect(url = 'http://localhost:5000') {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    this.socket.on('connect', () => {
      console.log('✅ WebSocket 已连接')
      this.connected = true
    })

    this.socket.on('disconnect', () => {
      console.log('❌ WebSocket 已断开')
      this.connected = false
    })

    this.socket.on('connection_response', (data) => {
      console.log('连接响应:', data)
    })

    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback)
      if (!this.listeners.has(event)) {
        this.listeners.set(event, [])
      }
      this.listeners.get(event).push(callback)
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback)
      if (this.listeners.has(event)) {
        const callbacks = this.listeners.get(event)
        const index = callbacks.indexOf(callback)
        if (index > -1) {
          callbacks.splice(index, 1)
        }
      }
    }
  }

  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data)
    }
  }
}

export default new WebSocketService()
