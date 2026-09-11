import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [isJoined, setIsJoined] = useState(false)
  const [username, setUsername] = useState('')
  const [roomId, setRoomId] = useState('')
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [alert, setAlert] = useState(null)
  
  const ws = useRef(null)
  const messagesEndRef = useRef(null)
  const containerRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleJoin = (e) => {
    e.preventDefault()
    if (!username.trim() || !roomId.trim()) return

    // Connect to FastAPI WebSocket
    ws.current = new WebSocket(`ws://localhost:8000/chat/${roomId}`)
    
    ws.current.onopen = () => {
      setIsJoined(true)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'alert') {
        // Show bullying alert and shake container
        setAlert(data.message)
        containerRef.current?.classList.add('shake')
        setTimeout(() => {
          setAlert(null)
          containerRef.current?.classList.remove('shake')
        }, 3000)
      } else if (data.type === 'message') {
        setMessages(prev => [...prev, data])
      }
    }

    ws.current.onclose = () => {
      setIsJoined(false)
    }
  }

  const handleLeave = () => {
    if (ws.current) {
      ws.current.close()
    }
    setIsJoined(false)
    setMessages([])
  }

  const sendMessage = (e) => {
    e.preventDefault()
    if (!inputText.trim() || !ws.current) return

    ws.current.send(JSON.stringify({
      username: username,
      text: inputText
    }))
    
    setInputText('')
  }

  return (
    <div className="glass-container" ref={containerRef}>
      {alert && <div className="alert-notification">{alert}</div>}
      
      {!isJoined ? (
        <div className="app-container">
          <div className="header">
            <h1>SafeChat</h1>
            <p>Join a secure, bully-free room</p>
          </div>
          
          <form className="login-form" onSubmit={handleJoin}>
            <div className="input-group">
              <label>Username</label>
              <input 
                type="text" 
                placeholder="Enter your name"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
              />
            </div>
            
            <div className="input-group">
              <label>Room ID</label>
              <input 
                type="text" 
                placeholder="Enter room ID (e.g., global)"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
              />
            </div>
            
            <button type="submit">Join Room</button>
          </form>
        </div>
      ) : (
        <div className="chat-room">
          <div className="room-header">
            <div>
              <span className="room-badge">Room: {roomId}</span>
            </div>
            <button className="leave-btn" onClick={handleLeave}>Leave</button>
          </div>
          
          <div className="message-list">
            {messages.length === 0 ? (
              <div style={{textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem'}}>
                No messages yet. Say hello!
              </div>
            ) : (
              messages.map((msg, i) => {
                const isOwn = msg.username === username;
                return (
                  <div key={i} className={`message-wrapper ${isOwn ? 'own' : 'other'}`}>
                    <div className="message-sender">{isOwn ? 'You' : msg.username}</div>
                    <div className="message-bubble">{msg.text}</div>
                  </div>
                )
              })
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <form className="input-area" onSubmit={sendMessage}>
            <input 
              type="text" 
              placeholder="Type a message..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              autoFocus
            />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </div>
  )
}

export default App
