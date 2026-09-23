import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom"

import { AuthProvider } from "./auth/AuthContext"
import ProtectedRoute from "./auth/ProtectedRoute"
import ErrorBoundary from "./components/ErrorBoundary"
import Layout from "./components/Layout"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Dashboard from "./pages/Dashboard"
import Opportunities from "./pages/Opportunities"
import Sources from "./pages/Sources"

export default function App() {
  return (
    // Outside the router, so it catches errors thrown by any route.
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/sources" element={<Sources />} />
              </Route>
            </Route>

            {/* Any unknown path goes home rather than rendering nothing.
                Vercel now rewrites every path to index.html (see
                frontend/vercel.json), so unmatched URLs reach the router
                instead of the host's 404 page — this decides what the
                router does with them. */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
