/**
 * MedicationForm Component
 * 
 * Form for creating and editing medications with validation
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Save, X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'
import { MedicationService, MedicationUtils, type ApiError } from '@/lib/api/medications'
import { components } from '@contracts/types/api'

type MedicationResponse = components['schemas']['MedicationResponse']
type MedicationCreate = components['schemas']['MedicationCreate']
type MedicationUpdate = components['schemas']['MedicationUpdate']

interface MedicationFormProps {
  medication?: MedicationResponse
  onSave?: (medication: MedicationResponse) => void
  onCancel?: () => void
  className?: string
}

interface FormData {
  name: string
  description: string
  is_active: boolean
}

interface FormErrors {
  name?: string
  description?: string
  general?: string
}

export function MedicationForm({ 
  medication, 
  onSave, 
  onCancel,
  className 
}: MedicationFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: medication?.name || '',
    description: medication?.description || '',
    is_active: medication?.is_active ?? true
  })
  
  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<ApiError | null>(null)

  const isEditing = !!medication

  // Update form data when medication prop changes
  useEffect(() => {
    if (medication) {
      setFormData({
        name: medication.name,
        description: medication.description || '',
        is_active: medication.is_active
      })
    }
  }, [medication])

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Validate name
    const nameValidation = MedicationUtils.validateMedicationName(formData.name)
    if (!nameValidation.valid) {
      newErrors.name = nameValidation.message
    }

    // Validate description
    const descriptionValidation = MedicationUtils.validateMedicationDescription(formData.description)
    if (!descriptionValidation.valid) {
      newErrors.description = descriptionValidation.message
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)
    setApiError(null)

    try {
      let result: MedicationResponse

      if (isEditing && medication) {
        // Update existing medication
        const updateData: MedicationUpdate = {
          name: formData.name !== medication.name ? formData.name : undefined,
          description: formData.description !== (medication.description || '') 
            ? (formData.description || null) 
            : undefined,
          is_active: formData.is_active !== medication.is_active ? formData.is_active : undefined
        }
        
        // Only send update if there are actual changes
        const hasChanges = Object.values(updateData).some(value => value !== undefined)
        if (!hasChanges) {
          onCancel?.()
          return
        }

        result = await MedicationService.updateMedication(medication.id, updateData)
      } else {
        // Create new medication
        const createData: MedicationCreate = {
          name: formData.name,
          description: formData.description || null,
          is_active: formData.is_active
        }
        
        result = await MedicationService.createMedication(createData)
      }

      onSave?.(result)
    } catch (error) {
      const apiErr = error as ApiError
      setApiError(apiErr)
      
      // Handle validation errors from the API
      if (apiErr.status === 422 && apiErr.details?.detail) {
        const newErrors: FormErrors = {}
        
        // Parse validation errors from FastAPI
        for (const validationError of apiErr.details.detail) {
          if (validationError.loc.includes('name')) {
            newErrors.name = validationError.msg
          } else if (validationError.loc.includes('description')) {
            newErrors.description = validationError.msg
          }
        }
        
        if (Object.keys(newErrors).length > 0) {
          setErrors(newErrors)
        }
      } else if (apiErr.status === 409) {
        // Handle duplicate name error
        setErrors({ name: 'A medication with this name already exists' })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear errors for the field being edited
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
    
    // Clear general API error when user starts editing
    if (apiError) {
      setApiError(null)
    }
  }

  const handleReset = () => {
    if (medication) {
      setFormData({
        name: medication.name,
        description: medication.description || '',
        is_active: medication.is_active
      })
    } else {
      setFormData({
        name: '',
        description: '',
        is_active: true
      })
    }
    setErrors({})
    setApiError(null)
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>
          {isEditing ? `Edit ${medication?.name}` : 'Add New Medication'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* General API Error */}
          {apiError && !errors.name && !errors.description && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <div className="ml-2">
                <h4 className="text-sm font-medium text-red-800">Error saving medication</h4>
                <p className="text-sm text-red-700 mt-1">{apiError.message}</p>
              </div>
            </Alert>
          )}

          {/* Name Field */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-sm font-medium">
              Medication Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter medication name"
              className={errors.name ? 'border-red-300 focus:border-red-500' : ''}
              required
            />
            {errors.name && (
              <p className="text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          {/* Description Field */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium">
              Description
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Optional description (e.g., 'Pain reliever and anti-inflammatory')"
              rows={3}
              className={errors.description ? 'border-red-300 focus:border-red-500' : ''}
            />
            {errors.description && (
              <p className="text-sm text-red-600">{errors.description}</p>
            )}
            <p className="text-xs text-gray-500">
              Maximum 500 characters
            </p>
          </div>

          {/* Active Status Field */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Status</Label>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="is_active"
                  checked={formData.is_active === true}
                  onChange={() => handleInputChange('is_active', true)}
                  className="mr-2"
                />
                <span className="text-sm">Active</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="is_active"
                  checked={formData.is_active === false}
                  onChange={() => handleInputChange('is_active', false)}
                  className="mr-2"
                />
                <span className="text-sm">Inactive</span>
              </label>
            </div>
            <p className="text-xs text-gray-500">
              Only active medications will be available for logging
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-between pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleReset}
              disabled={loading}
            >
              Reset
            </Button>
            <div className="flex items-center space-x-2">
              {onCancel && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={onCancel}
                  disabled={loading}
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              )}
              <Button
                type="submit"
                disabled={loading}
              >
                <Save className="w-4 h-4 mr-2" />
                {loading 
                  ? 'Saving...' 
                  : isEditing 
                    ? 'Update Medication' 
                    : 'Create Medication'
                }
              </Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export default MedicationForm