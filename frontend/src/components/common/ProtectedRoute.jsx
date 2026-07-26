import { Navigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

// children = whatever page is inside this component in App.jsx
// If logged in: render the page normally
// If not logged in: redirect to /login instantly
export default function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuthStore()

  if (!isLoggedIn) {
    // Navigate replaces the current page with /login
    // replace=true: the /myspace URL is removed from browser history (can't press Back to it)
    return <Navigate to="/login" replace />
  }

  return children
}