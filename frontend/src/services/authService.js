import api from './api'

const authService = {
  // Send register data to POST /auth/register
  // Returns: { access_token, token_type, user }
  async register(email, password, fullName = '') {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName || null,
    })
    return response.data
  },

  // Send login data to POST /auth/login
  // Returns: { access_token, token_type, user }
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  // Get the current user's profile from GET /auth/me
  // The token is attached automatically by the api.js interceptor
  // Returns: { id, email, full_name }
  async getMe() {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export default authService