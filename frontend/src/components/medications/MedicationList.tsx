/**
 * MedicationList Component
 * 
 * Displays a paginated, searchable list of medications with management actions
 */

'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Plus, Edit, Trash2, MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert } from '@/components/ui/alert'
import { MedicationService, type ApiError } from '@/lib/api/medications'
import { components } from '@contracts/types/api'

type MedicationResponse = components['schemas']['MedicationResponse']
type MedicationListResponse = components['schemas']['MedicationListResponse']

interface MedicationListProps {
  onEditMedication?: (medication: MedicationResponse) => void
  onCreateMedication?: () => void
  onDeleteMedication?: (id: number) => void
  className?: string
}

interface ListState {
  medications: MedicationResponse[]
  total: number
  page: number
  per_page: number
  pages: number
}

export function MedicationList({ 
  onEditMedication, 
  onCreateMedication, 
  onDeleteMedication,
  className 
}: MedicationListProps) {
  const [listState, setListState] = useState<ListState>({
    medications: [],
    total: 0,
    page: 1,
    per_page: 10,
    pages: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)

  // Debounced search effect
  const [searchDebounced, setSearchDebounced] = useState(searchQuery)
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchDebounced(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const loadMedications = useCallback(async (
    page = 1, 
    search = searchDebounced, 
    is_active = activeFilter
  ) => {
    try {
      setLoading(true)
      setError(null)

      const response = await MedicationService.listMedications({
        search: search || undefined,
        is_active,
        page,
        per_page: listState.per_page
      })

      setListState({
        medications: response.items,
        total: response.total,
        page: response.page,
        per_page: response.per_page,
        pages: response.pages
      })
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }, [searchDebounced, activeFilter, listState.per_page])

  // Load medications on component mount and when search/filter changes
  useEffect(() => {
    loadMedications(1)
  }, [loadMedications])

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= listState.pages) {
      loadMedications(newPage)
    }
  }

  const handleDeactivate = async (medication: MedicationResponse) => {
    try {
      setLoading(true)
      await MedicationService.deactivateMedication(medication.id)
      // Reload the current page to reflect changes
      loadMedications(listState.page)
    } catch (err) {
      setError(err as ApiError)
      setLoading(false)
    }
  }

  const handleReactivate = async (medication: MedicationResponse) => {
    try {
      setLoading(true)
      await MedicationService.reactivateMedication(medication.id)
      // Reload the current page to reflect changes
      loadMedications(listState.page)
    } catch (err) {
      setError(err as ApiError)
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (error) {
    return (
      <Alert className={className}>
        <div className="flex items-start space-x-2">
          <div className="flex-1">
            <h4 className="text-sm font-medium text-red-800">Error loading medications</h4>
            <p className="text-sm text-red-700 mt-1">{error.message}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadMedications(listState.page)}
          >
            Retry
          </Button>
        </div>
      </Alert>
    )
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Medication Master Data</CardTitle>
            {onCreateMedication && (
              <Button onClick={onCreateMedication}>
                <Plus className="w-4 h-4 mr-2" />
                Add Medication
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Search and Filter Controls */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search medications..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={activeFilter === undefined ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveFilter(undefined)}
              >
                All
              </Button>
              <Button
                variant={activeFilter === true ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveFilter(true)}
              >
                Active
              </Button>
              <Button
                variant={activeFilter === false ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveFilter(false)}
              >
                Inactive
              </Button>
            </div>
          </div>

          {/* Medications List */}
          <div className="space-y-4">
            {loading ? (
              // Loading skeletons
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-64" />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-8 w-8" />
                  </div>
                </div>
              ))
            ) : listState.medications.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {searchQuery || activeFilter !== undefined ? (
                  <>
                    <p>No medications found matching your criteria.</p>
                    <Button 
                      variant="link" 
                      onClick={() => {
                        setSearchQuery('')
                        setActiveFilter(undefined)
                      }}
                      className="mt-2"
                    >
                      Clear filters
                    </Button>
                  </>
                ) : (
                  <>
                    <p>No medications added yet.</p>
                    {onCreateMedication && (
                      <Button onClick={onCreateMedication} className="mt-2">
                        Add your first medication
                      </Button>
                    )}
                  </>
                )}
              </div>
            ) : (
              listState.medications.map((medication) => (
                <div
                  key={medication.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium">{medication.name}</h3>
                      <Badge variant={medication.is_active ? "default" : "secondary"}>
                        {medication.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    {medication.description && (
                      <p className="text-sm text-gray-600 mb-2">{medication.description}</p>
                    )}
                    <div className="text-xs text-gray-400">
                      Created {formatDate(medication.created_at)} • 
                      Updated {formatDate(medication.updated_at)}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {onEditMedication && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEditMedication(medication)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                    )}
                    
                    {medication.is_active ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeactivate(medication)}
                      >
                        Deactivate
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReactivate(medication)}
                      >
                        Reactivate
                      </Button>
                    )}

                    {onDeleteMedication && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDeleteMedication(medication.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {listState.pages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="text-sm text-gray-600">
                Showing {((listState.page - 1) * listState.per_page) + 1} to{' '}
                {Math.min(listState.page * listState.per_page, listState.total)} of{' '}
                {listState.total} medications
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(listState.page - 1)}
                  disabled={listState.page === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <span className="text-sm font-medium">
                  Page {listState.page} of {listState.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(listState.page + 1)}
                  disabled={listState.page === listState.pages}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default MedicationList