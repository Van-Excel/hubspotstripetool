import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/providers/auth-provider'
import { ProtectedRoute } from '@/components/protected-route'
import { AppLayout } from '@/components/layout/app-layout'
import LoginPage from '@/pages/login'
import DashboardPage from '@/pages/dashboard'
import AnomaliesPage from '@/pages/anomalies'
import PaymentsPage from '@/pages/payments'
import DealsPage from '@/pages/deals'
import CustomersPage from '@/pages/customers'
import AuditPage from '@/pages/audit'
import AdminUsersPage from '@/pages/admin/users'
import { Toaster } from 'sonner'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/anomalies" element={<AnomaliesPage />} />
              <Route path="/payments" element={<PaymentsPage />} />
              <Route path="/deals" element={<DealsPage />} />
              <Route path="/customers" element={<CustomersPage />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/admin/users" element={<AdminUsersPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}
