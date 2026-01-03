
import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState([])
  const [videoUrl, setVideoUrl] = useState(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    connect()
    return () => {
      if (ws.current) ws.current.close()
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const connect = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws')

    ws.current.onopen = () => {
      setConnected(true)
      addMessage('system', 'Connected to Agent Server.')
    }

    ws.current.onclose = () => {
      setConnected(false)
      addMessage('error', 'Disconnected. Reconnecting in 3s...')
      setTimeout(connect, 3000)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }
  }

  const handleMessage = (data) => {
    switch (data.type) {
      case 'video':
        setVideoUrl(data.url)
        break
      case 'status':
      case 'log':
      case 'error':
        addMessage(data.type, data.content)
        break
      default:
        console.log('Unknown message type:', data)
    }
  }

  const addMessage = (type, content) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date() }])
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!prompt.trim() || !connected) return

    setVideoUrl(null) // Reset video on new request
    addMessage('user', `> ${prompt}`)
    ws.current.send(JSON.stringify({ type: 'prompt', content: prompt }))
    setPrompt('')
  }

  return (
    <div className="app-container">
      <header>
        <h1>ZeroStick Agent</h1>
        <div className={`status-indicator ${connected ? 'online' : 'offline'}`}>
          {connected ? 'Online' : 'Offline'}
        </div>
      </header>

      <div className="main-content">
        <div className="terminal-window">
          <div className="terminal-content">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.type}`}>
                <span className="timestamp">[{msg.timestamp.toLocaleTimeString()}]</span>
                <span className="content">{msg.content}</span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-area">
            <span className="prompt-char">$</span>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter animation command (e.g. 'Make a stickman jump')"
              disabled={!connected}
              autoFocus
            />
          </form>
        </div>

        <div className="video-panel">
          {videoUrl ? (
            <div className="video-wrapper">
              <h3>Generated Animation</h3>
              <video src={videoUrl} controls autoPlay loop key={videoUrl} />
            </div>
          ) : (
            <div className="placeholder">
              <p>Waiting for generation...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
