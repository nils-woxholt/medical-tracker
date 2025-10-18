/**
 * MedicationManagement Component
 * 
 * Complete medication management interface with list, form, and modal functionality
 */

'use client'

import React, { useState } from 'react'
import { Plus, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MedicationList from './MedicationList'
import MedicationForm from './MedicationForm'
import { components } from '@contracts/types/api'

type MedicationResponse = components['schemas']['MedicationResponse']

interface MedicationManagementProps {
  className?: string
}

type ViewMode = 'list' | 'create' | 'edit'

export function MedicationManagement({ className }: MedicationManagementProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [editingMedication, setEditingMedication] = useState<MedicationResponse | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleCreateMedication = () => {
    setEditingMedication(null)
    setViewMode('create')
  }

  const handleEditMedication = (medication: MedicationResponse) => {
    setEditingMedication(medication)
    setViewMode('edit')
  }

  const handleSaveMedication = (medication: MedicationResponse) => {
    setViewMode('list')
    setEditingMedication(null)
    // Force refresh of the medication list
    setRefreshKey(prev => prev + 1)
  }

  const handleCancelForm = () => {
    setViewMode('list')
    setEditingMedication(null)
  }

  const handleDeleteMedication = (id: number) => {
    // Find medication name for confirmation dialog
    // In a real app, you might want to pass the medication object or fetch it
    setDeleteConfirm({ id, name: `Medication #${id}` })
  }

  const handleConfirmDelete = async () => {
    if (!deleteConfirm) return

    try {
      // Note: This uses the delete endpoint which might be admin-only
      // In most cases, you'd use deactivation instead
      // await MedicationService.deleteMedication(deleteConfirm.id)
      // Attempting to delete medication
      
      setDeleteConfirm(null)
      setRefreshKey(prev => prev + 1)
    } catch (error) {
      console.error('Error deleting medication:', error)
      // Handle error appropriately
    }
  }

  const renderContent = () => {
    switch (viewMode) {
      case 'create':
        return (
          <MedicationForm
            onSave={handleSaveMedication}
            onCancel={handleCancelForm}
          />
        )
      
      case 'edit':
        return (
          <MedicationForm
            medication={editingMedication || undefined}
            onSave={handleSaveMedication}
            onCancel={handleCancelForm}
          />
        )
      
      default:
        return (
          <MedicationList
            key={refreshKey}
            onCreateMedication={handleCreateMedication}
            onEditMedication={handleEditMedication}
            onDeleteMedication={handleDeleteMedication}
          />
        )
    }
  }

  return (
    <div className={className}>
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Medication Master Data
            </h1>
            <p className="text-gray-600 mt-1">
              Manage the list of medications available for logging
            </p>
          </div>
          
          {viewMode === 'list' && (
            <Button onClick={handleCreateMedication}>
              <Plus className="w-4 h-4 mr-2" />
              Add Medication
            </Button>
          )}
          
          {viewMode !== 'list' && (
            <Button variant="outline" onClick={handleCancelForm}>
              Back to List
            </Button>
          )}
        </div>
      </div>

      {/* Main Content */}
      {renderContent()}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-6 h-6 text-red-600" />
                <CardTitle className="text-red-800">Confirm Deletion</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-4">
                Are you sure you want to permanently delete "{deleteConfirm.name}"? 
                This action cannot be undone.
              </p>
              <p className="text-sm text-gray-600 mb-6">
                Consider deactivating the medication instead if it might be needed in the future.
              </p>
              <div className="flex items-center justify-end space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setDeleteConfirm(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleConfirmDelete}
                >
                  Delete Permanently
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default MedicationManagement