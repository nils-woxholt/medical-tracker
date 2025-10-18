"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

// Types from our generated API types
import type { components } from "../../../../../contracts/types/api";

type DoctorCreate = components["schemas"]["DoctorCreate"];

interface DoctorFormProps {
  onSubmit?: (doctor: DoctorCreate) => Promise<void>;
  onCancel?: () => void;
  className?: string;
}

export function DoctorForm({ onSubmit, onCancel, className }: DoctorFormProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<DoctorCreate>({
    name: "",
    specialty: null,
    phone: null,
    email: null,
    address: null,
    notes: null,
    is_active: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      return;
    }

    setLoading(true);
    try {
      await onSubmit?.(formData);
      
      // Reset form
      setFormData({
        name: "",
        specialty: null,
        phone: null,
        email: null,
        address: null,
        notes: null,
        is_active: true,
      });
    } catch (error) {
      console.error("Failed to create doctor:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: "",
      specialty: null,
      phone: null,
      email: null,
      address: null,
      notes: null,
      is_active: true,
    });
    onCancel?.();
  };

  return (
    <div className={className}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-2">
          <Label htmlFor="doctor-name">
            Doctor Name <span className="text-red-500">*</span>
          </Label>
          <Input
            id="doctor-name"
            placeholder="e.g., Dr. Jane Smith"
            value={formData.name}
            onChange={(e) => setFormData((prev: DoctorCreate) => ({ ...prev, name: e.target.value }))}
            required
            aria-describedby="doctor-name-help"
          />
          <p id="doctor-name-help" className="text-xs text-gray-600">
            Enter the full name of the healthcare provider
          </p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="specialty">Specialty</Label>
          <Input
            id="specialty"
            placeholder="e.g., Cardiology, Internal Medicine"
            value={formData.specialty || ""}
            onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
              ...prev, 
              specialty: e.target.value || null 
            }))}
            aria-describedby="specialty-help"
          />
          <p id="specialty-help" className="text-xs text-gray-600">
            Medical specialty or area of expertise
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="+1-555-123-4567"
              value={formData.phone || ""}
              onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
                ...prev, 
                phone: e.target.value || null 
              }))}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="doctor@clinic.com"
              value={formData.email || ""}
              onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
                ...prev, 
                email: e.target.value || null 
              }))}
            />
          </div>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="address">Address</Label>
          <Textarea
            id="address"
            placeholder="123 Medical Center Drive, Suite 456"
            value={formData.address || ""}
            onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
              ...prev, 
              address: e.target.value || null 
            }))}
            rows={2}
            aria-describedby="address-help"
          />
          <p id="address-help" className="text-xs text-gray-600">
            Office or clinic address
          </p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            placeholder="Additional notes about this doctor..."
            value={formData.notes || ""}
            onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
              ...prev, 
              notes: e.target.value || null 
            }))}
            rows={3}
            aria-describedby="notes-help"
          />
          <p id="notes-help" className="text-xs text-gray-600">
            Optional: Any additional information or notes
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => setFormData((prev: DoctorCreate) => ({ 
              ...prev, 
              is_active: e.target.checked 
            }))}
            className="h-4 w-4 rounded border-gray-300"
          />
          <Label htmlFor="is_active" className="text-sm">
            This doctor is currently active
          </Label>
        </div>

        <div className="flex gap-4 pt-4">
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !formData.name.trim()}>
            {loading ? "Adding..." : "Add Doctor"}
          </Button>
        </div>
      </form>
    </div>
  );
}