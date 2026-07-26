import { create } from 'zustand'

// create() defines the store
// (set) is the function you call to update the store
// Every component that calls useAuthStore() gets access to everything here
const useAuthStore = create((set) => ({

  // ── State ──────────────────────────────────────────────
  user:       null,   // { id, email, full_name }
  token:      null,   // the JWT token string
  isLoggedIn: false,

  // ── Actions (functions that update the state) ──────────

  // Called after successful login or register
  // Saves to state AND to localStorage (so login persists after browser refresh)
  login: (user, token) => {
    localStorage.setItem('forge_token', token)
    localStorage.setItem('forge_user', JSON.stringify(user))
    set({ user, token, isLoggedIn: true })
  },

  // Called when user clicks logout
  // Clears state AND localStorage
  logout: () => {
    localStorage.removeItem('forge_token')
    localStorage.removeItem('forge_user')
    set({ user: null, token: null, isLoggedIn: false })
  },

  // Called ONCE when the app first loads
  // Checks localStorage to restore login state if the user was previously logged in
  // This is why you stay logged in after closing and reopening the browser
  init: () => {
    const token = localStorage.getItem('forge_token')
    const userStr = localStorage.getItem('forge_user')
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        set({ user, token, isLoggedIn: true })
      } catch {
        // If stored data is corrupted, just clear it
        localStorage.removeItem('forge_token')
        localStorage.removeItem('forge_user')
      }
    }
  },
}))

export default useAuthStore