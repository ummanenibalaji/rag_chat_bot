const BASE = '/api'

export const getConversations = async (token) => {
  const res = await fetch(`${BASE}/conversations`, { headers: { token } })
  return res.json()
}

export const getMessages = async (convId, token) => {
  const res = await fetch(`${BASE}/messages/${convId}`, { headers: { token } })
  return res.json()
}

export const deleteConversation = async (convId, token) => {
  const res = await fetch(`${BASE}/conversations/${convId}`, {
    method: 'DELETE',
    headers: { token },
  })
  return res.json()
}

export const askStream = async ({ query, chatHistory, conversationId, selectedFile, token, onChunk, onDone, onConversationId }) => {
  const res = await fetch(`${BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', token },
    body: JSON.stringify({
      query,
      chat_history: chatHistory,
      conversation_id: conversationId,
      selected_file: selectedFile,
    }),
  })

  const convId = res.headers.get('conversation_id')
  if (convId) onConversationId?.(convId)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let full = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    full += chunk
    onChunk?.(full)
  }

  onDone?.(full)
  return full
}
