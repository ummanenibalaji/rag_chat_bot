import { useState } from 'react'
import Sidebar from './Sidebar'
import ChatArea from '../Chat/ChatArea'

export default function AppLayout() {
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [activeConvId, setActiveConvId] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const handleConversationSelect = (id, msgs) => {
    setActiveConvId(id)
    setConversationId(id)
    setMessages(msgs)
  }

  const handleNewChat = () => {
    setMessages([])
    setConversationId(null)
    setActiveConvId(null)
  }

  return (
    <div className="flex h-screen overflow-hidden mesh-bg">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 h-full">
        <Sidebar
          onConversationSelect={handleConversationSelect}
          activeConvId={activeConvId}
          onNewChat={handleNewChat}
          selectedFile={selectedFile}
          onFileSelect={setSelectedFile}
        />
      </div>

      {/* Main chat */}
      <div className="flex-1 h-full overflow-hidden">
        <ChatArea
          messages={messages}
          setMessages={setMessages}
          conversationId={conversationId}
          setConversationId={setConversationId}
          selectedFile={selectedFile}
        />
      </div>
    </div>
  )
}
