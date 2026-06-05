import api from './client'

export const getFiles = () => api.get('/files')

export const getDocuments = () => api.get('/documents')

export const uploadFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteFile = (filename) =>
  api.delete('/delete-file', { params: { filename } })
