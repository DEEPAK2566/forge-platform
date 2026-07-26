import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Find <div id="root"> in index.html — inject the whole React app there
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)