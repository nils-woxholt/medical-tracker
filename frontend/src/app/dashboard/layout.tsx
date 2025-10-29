import { Sidebar } from '@/components/dashboard/sidebar'
import { Header } from '@/components/dashboard/header'
import ProtectedLayout from '../(protected)/layout'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedLayout>
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <Sidebar className="w-64 bg-white shadow-sm" />
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          {/* Demo banner removed */}
          <main className="p-4 flex-1 bg-muted/20">{children}</main>
        </div>
      </div>
    </ProtectedLayout>
  );
}