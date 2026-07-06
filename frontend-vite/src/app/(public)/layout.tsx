import { Outlet } from 'react-router-dom'
import Header from '@/components/layout/Header'

/**
 * PublicLayout — wraps every public-facing page.
 * Renders the Header above the page content.
 * No auth guard — anyone can access public routes.
 */
export default function PublicLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
