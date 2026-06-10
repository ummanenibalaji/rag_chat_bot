import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useMotionValue, useSpring } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { getConversations, getMessages, deleteConversation } from '../../api/chat'
import { getFiles, uploadFile, deleteFile } from '../../api/files'
import Spinner from '../UI/Spinner'

const FILE_COLORS = {
  pdf: '#FF4466', png: '#00D4FF', jpg: '#00D4FF', jpeg: '#00D4FF',
  docx: '#4488FF', txt: '#8B9DC3', csv: '#00FF88', xlsx: '#00CC66', pptx: '#FF8800',
}
function fileColor(name) { return FILE_COLORS[name.split('.').pop()?.toLowerCase()] || '#4466AA' }

function FileDocIcon({ name, size = 13 }) {
  const ext = name.split('.').pop()?.toLowerCase()
  const c = fileColor(name)
  if (['png','jpg','jpeg'].includes(ext)) return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
    </svg>
  )
  if (ext === 'csv' || ext === 'xlsx') return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
      <line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>
    </svg>
  )
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg>
  )
}

/* ── 3D-tilt file item for knowledge base ── */
function TiltFileItem({ f, i, onDelete, deletingFile }) {
  const ref   = useRef(null)
  const rotX  = useMotionValue(0)
  const rotY  = useMotionValue(0)
  const liftY = useMotionValue(0)
  const sRotX  = useSpring(rotX,  { stiffness:320, damping:28 })
  const sRotY  = useSpring(rotY,  { stiffness:320, damping:28 })
  const sLiftY = useSpring(liftY, { stiffness:280, damping:24 })
  const color  = fileColor(f.filename)

  const onMove = (e) => {
    const rect = ref.current.getBoundingClientRect()
    const cx = rect.left + rect.width  / 2
    const cy = rect.top  + rect.height / 2
    rotX.set(-(e.clientY - cy) / (rect.height / 2) * 5)
    rotY.set( (e.clientX - cx) / (rect.width  / 2) * 5)
    liftY.set(-3)
  }
  const onLeave = () => { rotX.set(0); rotY.set(0); liftY.set(0) }

  return (
    <motion.div
      initial={{ opacity:0, x:-5 }}
      animate={{ opacity:1, x:0 }}
      transition={{ delay: i * 0.04 }}
      style={{ perspective:'600px' }}
    >
      <motion.div
        ref={ref}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        style={{
          rotateX:sRotX, rotateY:sRotY, y:sLiftY,
          transformStyle:'preserve-3d',
        }}
        className="flex items-center gap-2 px-3 py-2 rounded-lg group transition-all duration-150"
        whileHover={{
          boxShadow:`0 6px 28px rgba(0,0,0,.45),0 0 20px ${color}12`,
          borderColor:`${color}18`,
          background:`${color}06`,
        }}
        style2={{ background:'rgba(0,212,255,0.018)', border:`1px solid rgba(0,212,255,0.05)` }}
        animate2={{ borderColor:'rgba(0,212,255,0.05)', background:'rgba(0,212,255,0.018)' }}
      >
        <div style={{
          display:'flex', alignItems:'center', gap:8, padding:'2px 4px', borderRadius:8,
          background:'rgba(0,212,255,0.018)', border:'1px solid rgba(0,212,255,0.05)',
          transition:'background .15s,border-color .15s,box-shadow .15s',
          width:'100%',
        }}
          onMouseEnter={e => {
            e.currentTarget.style.background = `${color}06`
            e.currentTarget.style.borderColor = `${color}18`
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(0,212,255,0.018)'
            e.currentTarget.style.borderColor = 'rgba(0,212,255,0.05)'
          }}
        >
          <div className="flex-shrink-0 relative">
            <FileDocIcon name={f.filename} size={12} />
            <div className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full"
              style={{ background:color, boxShadow:`0 0 5px ${color}` }} />
          </div>
          <span className="truncate flex-1 text-xs" style={{ color:'rgba(140,200,230,.5)' }}>{f.filename}</span>
          <button onClick={() => onDelete(f.filename)} disabled={deletingFile === f.filename}
            className="btn-danger-sm flex-shrink-0 opacity-0 group-hover:opacity-60"
            style={{ transition:'opacity .15s' }}>
            {deletingFile === f.filename ? <Spinner size={10} /> : (
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

/* ── Neon-trail conversation button ── */
function ConvButton({ conv, active, onClick, onDelete, i }) {
  const [hovered, setHovered] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    setDeleting(true)
    await onDelete(conv.id)
    setDeleting(false)
  }

  return (
    <motion.div
      initial={{ opacity:0, x:-10 }}
      animate={{ opacity:1, x:0 }}
      exit={{ opacity:0, x:-10, height:0, marginBottom:0 }}
      transition={{ delay: i * 0.03, ease:[.16,1,.3,1] }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      style={{ position:'relative' }}
    >
      <button
        className={`sidebar-conv-item ${active ? 'active' : ''}`}
        onClick={onClick}
        style={{ paddingRight: hovered ? '32px' : undefined, transition:'padding .15s' }}
        onMouseEnter={e => {
          if (!active) {
            e.currentTarget.style.background = 'rgba(0,212,255,0.04)'
            e.currentTarget.style.borderColor = 'rgba(0,212,255,0.1)'
            e.currentTarget.style.color = 'rgba(140,200,230,.65)'
            e.currentTarget.style.boxShadow = '0 2px 14px rgba(0,0,0,.3),inset 0 1px 0 rgba(0,212,255,.04)'
          }
        }}
        onMouseLeave={e => {
          if (!active) {
            e.currentTarget.style.background = ''
            e.currentTarget.style.borderColor = ''
            e.currentTarget.style.color = ''
            e.currentTarget.style.boxShadow = ''
          }
        }}
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0 mt-0.5 opacity-35">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span className="truncate text-xs leading-relaxed">{conv.title || 'Untitled'}</span>
      </button>

      {/* Delete button — appears on hover */}
      <AnimatePresence>
        {hovered && (
          <motion.button
            initial={{ opacity:0, scale:.7 }}
            animate={{ opacity:1, scale:1 }}
            exit={{ opacity:0, scale:.7 }}
            transition={{ duration:.12 }}
            onClick={handleDelete}
            disabled={deleting}
            style={{
              position:'absolute', right:6, top:'50%', transform:'translateY(-50%)',
              width:20, height:20, borderRadius:6,
              display:'flex', alignItems:'center', justifyContent:'center',
              background:'rgba(255,60,80,.08)',
              border:'1px solid rgba(255,60,80,.18)',
              color:'rgba(255,80,100,.6)',
              transition:'all .15s',
              flexShrink:0,
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'rgba(255,60,80,.16)'
              e.currentTarget.style.borderColor = 'rgba(255,60,80,.38)'
              e.currentTarget.style.color = 'rgba(255,80,100,.9)'
              e.currentTarget.style.boxShadow = '0 0 10px rgba(255,60,80,.2)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'rgba(255,60,80,.08)'
              e.currentTarget.style.borderColor = 'rgba(255,60,80,.18)'
              e.currentTarget.style.color = 'rgba(255,80,100,.6)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            {deleting
              ? <div style={{ width:8, height:8, border:'1.5px solid rgba(255,80,100,.5)', borderTopColor:'rgba(255,80,100,.9)', borderRadius:'50%', animation:'spin .6s linear infinite' }} />
              : <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
                </svg>
            }
          </motion.button>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function Sidebar({ onConversationSelect, activeConvId, onNewChat, selectedFile, onFileSelect }) {
  const { token, email, logout } = useAuth()
  const [conversations, setConversations] = useState([])
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [deletingFile, setDeletingFile] = useState(null)
  const [section, setSection] = useState('chats')
  const fileInputRef = useRef()

  const loadConversations = async () => {
    try { const data = await getConversations(token); setConversations(Array.isArray(data) ? data : []) } catch {}
  }
  const loadFiles = async () => {
    try { const { data } = await getFiles(); setFiles(Array.isArray(data) ? data : []) } catch {}
  }

  useEffect(() => { loadConversations(); loadFiles() }, [])

  const handleConvClick = async (conv) => {
    try { const msgs = await getMessages(conv.id, token); onConversationSelect(conv.id, Array.isArray(msgs) ? msgs : []) } catch {}
  }
  const handleDeleteConv = async (convId) => {
    try { await deleteConversation(convId, token); await loadConversations() } catch {}
  }
  const handleUpload = async (e) => {
    const file = e.target.files?.[0]; if (!file) return
    setUploading(true)
    try { await uploadFile(file); await loadFiles() } catch {}
    setUploading(false); fileInputRef.current.value = ''
  }
  const handleDelete = async (filename) => {
    setDeletingFile(filename)
    try { await deleteFile(filename); await loadFiles() } catch {}
    setDeletingFile(null)
  }

  const avatarLetter = email?.[0]?.toUpperCase() || '?'

  return (
    <div className="flex flex-col h-full" style={{
      background:'rgba(0,4,14,.96)',
      borderRight:'1px solid rgba(0,212,255,.08)',
      boxShadow:'4px 0 40px rgba(0,0,0,.5),inset -1px 0 0 rgba(0,212,255,.04)',
    }}>

      {/* Wordmark header */}
      <div className="px-5 pt-5 pb-4 border-b" style={{ borderColor:'rgba(0,212,255,.06)' }}>
        <div className="flex items-baseline gap-0 mb-1">
          <span style={{ fontWeight:900, fontSize:'1.35rem', letterSpacing:'-0.05em', lineHeight:1, color:'#fff',
            textShadow:'0 0 20px rgba(0,212,255,.25)' }}>DOC</span>
          <span className="ai-wordmark" style={{ fontWeight:900, fontSize:'1.35rem', letterSpacing:'-0.05em', lineHeight:1,
            filter:'drop-shadow(0 0 8px rgba(0,212,255,.4))' }}>ai</span>
        </div>
        <div className="flex items-center gap-2">
          <div style={{ width:1, height:10, background:'rgba(0,212,255,.3)' }} />
          <span className="data-stream" style={{ color:'rgba(0,212,255,.3)', letterSpacing:'.12em' }}>
            DOCUMENT INTELLIGENCE
          </span>
        </div>
      </div>

      {/* New Chat */}
      <div className="p-3">
        <motion.button
          whileHover={{ scale:1.015, boxShadow:'0 0 28px rgba(0,212,255,.14),inset 0 1px 0 rgba(0,212,255,.1)' }}
          whileTap={{ scale:.97 }}
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold"
          style={{
            background:'rgba(0,212,255,.06)', border:'1px solid rgba(0,212,255,.14)',
            color:'rgba(0,212,255,.75)', letterSpacing:'.04em', transition:'color .15s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'rgba(0,212,255,.95)'}
          onMouseLeave={e => e.currentTarget.style.color = 'rgba(0,212,255,.75)'}
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          NEW CONVERSATION
        </motion.button>
      </div>

      {/* Section tabs */}
      <div className="px-3 mb-2">
        <div className="flex gap-0.5 p-0.5 rounded-lg" style={{
          background:'rgba(0,0,0,.6)', border:'1px solid rgba(0,212,255,.06)',
        }}>
          {[['chats','Chats'],['files','Documents']].map(([key,label]) => (
            <button key={key} onClick={() => setSection(key)}
              className="flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all duration-200"
              style={section === key
                ? { background:'rgba(0,212,255,.1)', color:'rgba(0,212,255,.85)',
                    boxShadow:'0 0 14px rgba(0,212,255,.1),inset 0 1px 0 rgba(0,212,255,.06)',
                    border:'1px solid rgba(0,212,255,.12)' }
                : { color:'rgba(80,140,180,.35)', border:'1px solid transparent' }
              }
            >{label}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 pb-2">
        <AnimatePresence mode="wait">
          {section === 'chats' ? (
            <motion.div key="chats" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} transition={{ duration:.12 }}>
              {conversations.length === 0 ? (
                <HoloEmptyState icon={<ChatIcon />} text="No conversations yet" />
              ) : (
                <div className="space-y-0.5 pt-1">
                  <AnimatePresence>
                  {conversations.map((conv, i) => (
                    <ConvButton key={conv.id} conv={conv} i={i} active={activeConvId === conv.id}
                      onClick={() => handleConvClick(conv)} onDelete={handleDeleteConv} />
                  ))}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div key="files" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} transition={{ duration:.12 }}>
              {/* Upload */}
              <div className="mb-4 pt-1">
                <input ref={fileInputRef} type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.txt,.csv,.xlsx,.pptx"
                  onChange={handleUpload} className="hidden" />
                <motion.button
                  whileHover={{ scale:1.01, boxShadow:'0 0 24px rgba(0,212,255,.1)', borderColor:'rgba(0,212,255,.38)' }}
                  whileTap={{ scale:.97 }}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-medium"
                  style={{
                    border:'1px dashed rgba(0,212,255,.2)', color:'rgba(0,212,255,.65)',
                    background:'rgba(0,212,255,.025)', transition:'color .15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,212,255,.06)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(0,212,255,.025)'}
                >
                  {uploading ? <Spinner size={12} /> : (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
                    </svg>
                  )}
                  {uploading ? 'Uploading…' : 'Upload document'}
                </motion.button>
              </div>

              <HoloSectionLabel>Search scope</HoloSectionLabel>
              <div className="space-y-0.5 mb-4">
                <ScopeButton selected={!selectedFile} onClick={() => onFileSelect(null)}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  </svg>
                  All documents
                </ScopeButton>
                {files.map(f => (
                  <ScopeButton key={f.filename} selected={selectedFile === f.filename} onClick={() => onFileSelect(f.filename)}>
                    <FileDocIcon name={f.filename} size={10} />
                    <span className="truncate">{f.filename}</span>
                  </ScopeButton>
                ))}
              </div>

              {files.length > 0 && (
                <>
                  <HoloSectionLabel>Knowledge base</HoloSectionLabel>
                  <div className="space-y-0.5">
                    {files.map((f, i) => (
                      <TiltFileItem key={f.filename} f={f} i={i} onDelete={handleDelete} deletingFile={deletingFile} />
                    ))}
                  </div>
                </>
              )}

              {files.length === 0 && <HoloEmptyState icon={<DocIcon />} text="No documents uploaded" />}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* User footer */}
      <div className="p-3 border-t" style={{ borderColor:'rgba(0,212,255,.06)' }}>
        <div className="flex items-center gap-2.5 px-1">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{
              background:'linear-gradient(135deg,rgba(0,153,204,.8),rgba(0,212,255,.6),rgba(139,92,246,.5))',
              color:'white', boxShadow:'0 0 14px rgba(0,212,255,.3)',
              fontFamily:"'Space Grotesk',sans-serif", animation:'breathe 4s ease-in-out infinite',
            }}>
            {avatarLetter}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate" style={{ color:'rgba(140,200,230,.5)' }}>{email}</p>
          </div>
          <motion.button
            whileHover={{ color:'rgba(255,60,80,.7)', scale:1.12 }}
            whileTap={{ scale:.88 }}
            onClick={logout}
            className="btn-ghost p-1.5 rounded-lg"
            title="Sign out"
            style={{ color:'rgba(80,140,180,.4)' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
          </motion.button>
        </div>
      </div>
    </div>
  )
}

function HoloSectionLabel({ children }) {
  return (
    <div className="flex items-center gap-2 mb-1.5 px-1">
      <div style={{ width:12, height:1, background:'rgba(0,212,255,.25)' }} />
      <p className="data-stream" style={{ color:'rgba(0,212,255,.28)' }}>{children}</p>
    </div>
  )
}

function ScopeButton({ selected, onClick, children }) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={!selected ? { x:2 } : {}}
      className="w-full text-left px-3 py-2 rounded-lg text-xs flex items-center gap-2"
      style={selected
        ? { background:'rgba(0,212,255,.07)', color:'rgba(0,212,255,.75)',
            border:'1px solid rgba(0,212,255,.16)', boxShadow:'0 0 12px rgba(0,212,255,.06)',
            transition:'all .15s' }
        : { color:'rgba(80,140,180,.4)', border:'1px solid transparent', transition:'all .15s' }
      }
      onMouseEnter={e => { if (!selected) { e.currentTarget.style.color='rgba(140,200,230,.55)'; e.currentTarget.style.background='rgba(0,212,255,.03)' }}}
      onMouseLeave={e => { if (!selected) { e.currentTarget.style.color='rgba(80,140,180,.4)'; e.currentTarget.style.background='transparent' }}}
    >
      {children}
    </motion.button>
  )
}

function HoloEmptyState({ icon, text }) {
  return (
    <div className="text-center py-10">
      <div className="w-10 h-10 rounded-xl mx-auto mb-3 flex items-center justify-center"
        style={{ background:'rgba(0,212,255,.03)', border:'1px solid rgba(0,212,255,.07)' }}>
        {icon}
      </div>
      <p className="data-stream" style={{ color:'rgba(0,212,255,.22)' }}>{text}</p>
    </div>
  )
}

function ChatIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  )
}
function DocIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  )
}
