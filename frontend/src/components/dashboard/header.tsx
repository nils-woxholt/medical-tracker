/**
 * Dashboard Header Component
 */

'use client'

import { Bell, Search, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  return (
    <header className={`bg-white border-b px-6 py-4 ${className}`}>
      <div className="flex items-center justify-between">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search medications, logs..."
              className="pl-10"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
              3
            </span>
          </Button>

          {/* User Menu */}
          <div className="flex items-center space-x-3">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-gray-900">Demo User</p>
              <p className="text-xs text-gray-500">demo@example.com</p>
            </div>
            
            <Button variant="ghost" size="sm" className="p-1 rounded-full">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-blue-600" />
              </div>
            </Button>

            <Button variant="ghost" size="sm">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header