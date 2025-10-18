/**
 * MedicationSearch Component
 * 
 * Searchable dropdown component for selecting medications
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Search, ChevronDown, Check, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MedicationService } from '@/lib/api/medications'
import { components } from '@contracts/types/api'

type MedicationPublic = components['schemas']['MedicationPublic']

interface MedicationSearchProps {
  value?: MedicationPublic | null
  onSelect?: (medication: MedicationPublic | null) => void
  placeholder?: string
  disabled?: boolean
  className?: string
  allowClear?: boolean
  activeOnly?: boolean
}

export function MedicationSearch({ 
  value, 
  onSelect, 
  placeholder = "Search medications...",
  disabled = false,
  className = "",
  allowClear = true,
  activeOnly = true
}: MedicationSearchProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [medications, setMedications] = useState<MedicationPublic[]>([])
  const [loading, setLoading] = useState(false)
  
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Debounced search
  const [searchDebounced, setSearchDebounced] = useState('')
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchDebounced(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Load medications when search query changes
  useEffect(() => {
    const loadMedications = async () => {
      if (!searchDebounced && !isOpen) return

      setLoading(true)
      try {
        let results: MedicationPublic[]
        
        if (searchDebounced) {
          // Search for medications
          results = await MedicationService.searchMedications({
            q: searchDebounced,
            limit: 10
          })
        } else {
          // Get all active medications when dropdown opens without search
          results = activeOnly 
            ? await MedicationService.getActiveMedications()
            : (await MedicationService.listMedications({ 
                per_page: 50,
                is_active: activeOnly ? true : undefined 
              })).items.map(item => ({
                id: item.id,
                name: item.name,
                description: item.description,
                is_active: item.is_active
              }))
        }
        
        // Filter by active status if specified
        if (activeOnly) {
          results = results.filter(med => med.is_active)
        }
        
        setMedications(results)
      } catch (error) {
        console.error('Error loading medications:', error)
        setMedications([])
      } finally {
        setLoading(false)
      }
    }

    if (isOpen || searchDebounced) {
      loadMedications()
    }
  }, [searchDebounced, isOpen, activeOnly])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (medication: MedicationPublic) => {
    onSelect?.(medication)
    setIsOpen(false)
    setSearchQuery('')
  }

  const handleClear = () => {
    onSelect?.(null)
    setSearchQuery('')
    setIsOpen(false)
  }

  const handleInputFocus = () => {
    if (!disabled) {
      setIsOpen(true)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false)
      inputRef.current?.blur()
    }
  }

  return (
    <div ref={searchRef} className={`relative ${className}`}>
      {/* Selected medication display or search input */}
      {value && !isOpen ? (
        <div className="flex items-center justify-between border rounded-md px-3 py-2 bg-white">
          <div className="flex items-center space-x-2 flex-1">
            <span className="font-medium">{value.name}</span>
            {value.description && (
              <span className="text-sm text-gray-500 truncate">
                - {value.description}
              </span>
            )}
            <Badge variant={value.is_active ? "default" : "secondary"} className="text-xs">
              {value.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
          <div className="flex items-center space-x-1">
            {allowClear && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClear}
                disabled={disabled}
                className="p-1 h-6 w-6"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(true)}
              disabled={disabled}
              className="p-1 h-6 w-6"
            >
              <ChevronDown className="w-4 h-4" />
            </Button>
          </div>
        </div>
      ) : (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            ref={inputRef}
            type="text"
            placeholder={placeholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={handleInputFocus}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            className="pl-10 pr-10"
          />
          <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        </div>
      )}

      {/* Dropdown list */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
          {loading ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              Searching medications...
            </div>
          ) : medications.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              {searchQuery ? 'No medications found' : 'No medications available'}
            </div>
          ) : (
            <div className="py-1">
              {medications.map((medication) => (
                <button
                  key={medication.id}
                  type="button"
                  className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                  onClick={() => handleSelect(medication)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{medication.name}</span>
                        <Badge variant={medication.is_active ? "default" : "secondary"} className="text-xs">
                          {medication.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                      {medication.description && (
                        <div className="text-sm text-gray-500 mt-1">
                          {medication.description}
                        </div>
                      )}
                    </div>
                    {value && value.id === medication.id && (
                      <Check className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MedicationSearch