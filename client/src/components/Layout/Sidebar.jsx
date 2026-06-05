import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { getConversations, getMessages } from '../../api/chat'
import { getFiles, uploadFile, deleteFile } from '../../api/files'
import Spinner from '../UI/Spinner'

const FILE_ICONS = {
  pdf: { icon: '📄', color: '#EF4444' },
  png: { icon: '🖼', color: '#3B82F6' },
  jpg: { icon: '🖼', color: '#3B82F6' },
  jpeg: { icon: '🖼', color: '#3B82F6' },
  docx: { icon: '📝', color: '#2563EB' },
  txt: { icon: '📃', color: '#6B7280' },
  csv: { icon: '📊', color: '#10B981' },
  xlsx: { icon: '📊', color: '#059669' },
  pptx: { icon: '📋', color: '#F59E0B' },
}

function fileIcon(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  return FILE_ICONS[ext] || { icon: '📎', color: '#94A3B8' }
}

export default function Sidebar({ onConversationSelect, activeConvId, onNewChat, selectedFile, onFileSelect }) {
  const { token, email, logout } = useAuth()
  const [conversations, setConversations] = useState([])
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [deletingFile, setDeletingFile] = useState(null)
  const [section, setSection] = useState('chats') // 'chats' | 'files'
  const fileInputRef = useRef()

  const loadConversations = async () => {
    try {
      const data = await getConversations(token)
      setConversations(Array.isArray(data) ? data : [])
    } catch {}
  }

  const loadFiles = async () => {
    try {
      const { data } = await getFiles()
      setFiles(Array.isArray(data) ? data : [])
    } catch {}
  }

  useEffect(() => {
    loadConversations()
    loadFiles()
  }, [])

  const handleConvClick = async (conv) => {
    try {
      const msgs = await getMessages(conv.id, token)
      onConversationSelect(conv.id, Array.isArray(msgs) ? msgs : [])
    } catch {}
  }

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await uploadFile(file)
      await loadFiles()
    } catch {}
    setUploading(false)
    fileInputRef.current.value = ''
  }

  const handleDelete = async (filename) => {
    setDeletingFile(filename)
    try {
      await deleteFile(filename)
      await loadFiles()
    } catch {}
    setDeletingFile(null)
  }

  const avatarLetter = email?.[0]?.toUpperCase() || '?'

  return (
    <div className="flex flex-col h-full" style={{ background: 'rgba(6,11,24,0.95)', borderRight: '1px solid rgba(255,255,255,0.06)' }}>
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="font-bold text-sm text-gradient">DocuMind AI</span>
        </div>
      </div>

      {/* New Chat */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-medium transition-all duration-200"
          style={{
            background: 'rgba(99,102,241,0.1)',
            border: '1px solid rgba(99,102,241,0.2)',
            color: '#818CF8'
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.15)'; e.currentTarget.style.boxShadow = '0 0 12px rgba(99,102,241,0.2)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.1)'; e.currentTarget.style.boxShadow = 'none' }}
        >
          <span style={{ fontSize: 16 }}>+</span> New Chat
        </button>
      </div>

      {/* Tab Switch */}
      <div className="px-3 mb-2">
        <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'rgba(0,0,0,0.3)' }}>
          {[['chats', '💬', 'Chats'], ['files', '📁', 'Files']].map(([key, icon, label]) => (
            <button
              key={key}
              onClick={() => setSection(key)}
              className="flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all duration-150 flex items-center justify-center gap-1"
              style={section === key
                ? { background: 'rgba(99,102,241,0.2)', color: '#818CF8' }
                : { color: '#475569' }
              }
            >
              {icon} {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 pb-2">
        <AnimatePresence mode="wait">
          {section === 'chats' ? (
            <motion.div key="chats" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
              {conversations.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-3xl mb-2 opacity-30">💬</div>
                  <p className="text-xs" style={{ color: '#334155' }}>No conversations yet</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {conversations.map((conv) => (
                    <motion.button
                      key={conv.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`sidebar-conv-item ${activeConvId === conv.id ? 'active' : ''}`}
                      onClick={() => handleConvClick(conv)}
                    >
                      <span className="flex-shrink-0" style={{ fontSize: 12 }}>💬</span>
                      <span className="truncate text-xs leading-relaxed">{conv.title || 'Untitled'}</span>
                    </motion.button>
                  ))}
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div key="files" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
              {/* Upload button */}
              <div className="mb-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.txt,.csv,.xlsx,.pptx"
                  onChange={handleUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-medium transition-all duration-200"
                  style={{ border: '1px dashed rgba(99,102,241,0.3)', color: '#6366F1', background: 'rgba(99,102,241,0.05)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(99,102,241,0.05)'}
                >
                  {uploading ? <Spinner size={12} /> : <span>↑</span>}
                  {uploading ? 'Uploading...' : 'Upload Document'}
                </button>
              </div>

              {/* Search scope */}
              <div className="mb-2">
                <p className="text-xs font-medium mb-1.5" style={{ color: '#475569' }}>Search scope</p>
                <div className="space-y-1">
                  <button
                    onClick={() => onFileSelect(null)}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs transition-all duration-150 flex items-center gap-2"
                    style={!selectedFile
                      ? { background: 'rgba(99,102,241,0.1)', color: '#818CF8', border: '1px solid rgba(99,102,241,0.2)' }
                      : { color: '#64748B', border: '1px solid transparent' }
                    }
                  >
                    <span>🌐</span> All Documents
                  </button>
                  {files.map((f) => {
                    const { icon, color } = fileIcon(f.filename)
                    return (
                      <button
                        key={f.filename}
                        onClick={() => onFileSelect(f.filename)}
                        className="w-full text-left px-3 py-2 rounded-lg text-xs transition-all duration-150 flex items-center gap-2"
                        style={selectedFile === f.filename
                          ? { background: 'rgba(99,102,241,0.1)', color: '#818CF8', border: '1px solid rgba(99,102,241,0.2)' }
                          : { color: '#64748B', border: '1px solid transparent' }
                        }
                      >
                        <span style={{ color }}>{icon}</span>
                        <span className="truncate flex-1">{f.filename}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* File list with delete */}
              {files.length > 0 && (
                <>
                  <p className="text-xs font-medium mb-1.5 mt-3" style={{ color: '#475569' }}>Knowledge base</p>
                  <div className="space-y-1">
                    {files.map((f) => {
                      const { icon, color } = fileIcon(f.filename)
                      return (
                        <div
                          key={f.filename}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg group"
                          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}
                        >
                          <span style={{ color, fontSize: 13, flexShrink: 0 }}>{icon}</span>
                          <span className="truncate flex-1 text-xs" style={{ color: '#94A3B8' }}>{f.filename}</span>
                          <button
                            onClick={() => handleDelete(f.filename)}
                            disabled={deletingFile === f.filename}
                            className="btn-danger-sm flex-shrink-0 opacity-0 group-hover:opacity-100"
                          >
                            {deletingFile === f.filename ? <Spinner size={10} /> : '×'}
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </>
              )}

              {files.length === 0 && (
                <div className="text-center py-6">
                  <div className="text-3xl mb-2 opacity-30">📂</div>
                  <p className="text-xs" style={{ color: '#334155' }}>No documents yet</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* User footer */}
      <div className="p-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', color: 'white' }}>
            {avatarLetter}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate" style={{ color: '#E2E8F0' }}>{email}</p>
            <p className="text-xs" style={{ color: '#334155' }}>Signed in</p>
          </div>
          <button onClick={logout} className="btn-ghost p-1.5 rounded-lg" title="Logout">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
