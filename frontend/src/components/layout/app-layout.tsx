import { Outlet } from 'react-router-dom'
import { Sidebar } from './sidebar'
import { Header } from './header'

export function AppLayout() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-56 flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
