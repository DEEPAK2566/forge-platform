import axios from 'axios'

// Create a configured axios instance
// baseURL: every request automatically starts with this URL
// So api.post('/auth/login') sends to http://localhost:8000/auth/login
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor = runs before EVERY request automatically
// This one attaches the JWT token to every request as a header
// The backend's get_current_user dependency reads this header to identify the user
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('forge_token')
  if (token) {
    // Authorization: Bearer <token> is the standard format
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — runs after every response
// If the backend returns 401 (unauthorized), clear the stored token
// This handles expired tokens: user will be redirected to login
api.interceptors.response.use(
  (response) => response,   // success: just return the response
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('forge_token')
      localStorage.removeItem('forge_user')
      window.location.href = '/login'   // redirect to login
    }
    return Promise.reject(error)
  }
)

export default api