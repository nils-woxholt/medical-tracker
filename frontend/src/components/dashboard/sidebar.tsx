/**
 * Dashboard Sidebar Navigation Component
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Home, 
  PlusCircle, 
  Activity, 
  Calendar, 
  Pill,
  BarChart3,
  Settings,
  HelpCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface SidebarProps {
  className?: string
}

interface NavItem {
  href: string
  icon: React.ComponentType<{ className?: string }>
  label: string
  badge?: string
  description?: string
}

const navItems: NavItem[] = [
  {
    href: '/dashboard',
    icon: Home,
    label: 'Dashboard',
    description: 'Overview and quick actions'
  },
  {
    href: '/dashboard/log',
    icon: PlusCircle,
    label: 'Log Entry',
    description: 'Record medications and symptoms'
  },
  {
    href: '/dashboard/timeline',
    icon: Activity,
    label: 'Timeline',
    description: 'View your health history'
  },
  {
    href: '/dashboard/calendar',
    icon: Calendar,
    label: 'Calendar',
    description: 'Schedule and reminders'
  },
  {
    href: '/dashboard/medications',
    icon: Pill,
    label: 'Medications',
    description: 'Manage medication master data',
    badge: 'New'
  },
  {
    href: '/dashboard/analytics',
    icon: BarChart3,
    label: 'Analytics',
    description: 'Health insights and trends'
  }
]

const bottomNavItems: NavItem[] = [
  {
    href: '/dashboard/settings',
    icon: Settings,
    label: 'Settings'
  },
  {
    href: '/dashboard/help',
    icon: HelpCircle,
    label: 'Help & Support'
  }
]

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside className={`flex flex-col ${className}`}>
      {/* Logo/Brand */}
      <div className="p-6 border-b">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Pill className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">MedTracker</h1>
            <p className="text-xs text-gray-500">Health Management</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start h-auto p-3 ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 hover:bg-blue-100' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center w-full">
                    <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                    <div className="flex-1 text-left">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{item.label}</span>
                        {item.badge && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                      {item.description && (
                        <p className="text-xs text-gray-500 mt-1">
                          {item.description}
                        </p>
                      )}
                    </div>
                  </div>
                </Button>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div className="p-4 border-t">
        <div className="space-y-2">
          {bottomNavItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 hover:bg-blue-100' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  size="sm"
                >
                  <Icon className={`w-4 h-4 mr-3 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                  {item.label}
                </Button>
              </Link>
            )
          })}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar