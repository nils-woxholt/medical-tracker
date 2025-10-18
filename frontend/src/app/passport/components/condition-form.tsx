"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Types from our generated API types
import type { components } from "../../../../../contracts/types/api";

type ConditionCreate = components["schemas"]["ConditionCreate"];

interface ConditionFormProps {
  onSubmit?: (condition: ConditionCreate) => Promise<void>;
  onCancel?: () => void;
  className?: string;
}

export function ConditionForm({ onSubmit, onCancel, className }: ConditionFormProps) {
  const [loading, setLoading] = useState(false);
  const [diagnosedDate, setDiagnosedDate] = useState("");
  
  const [formData, setFormData] = useState<ConditionCreate>({
    name: "",
    description: "",
    severity: null,
    diagnosed_date: null,
    is_active: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      return;
    }

    setLoading(true);
    try {
      const submitData: ConditionCreate = {
        ...formData,
        diagnosed_date: diagnosedDate || null,
      };

      await onSubmit?.(submitData);
      
      // Reset form
      setFormData({
        name: "",
        description: "",
        severity: null,
        diagnosed_date: null,
        is_active: true,
      });
      setDiagnosedDate("");
    } catch (error) {
      console.error("Failed to create condition:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: "",
      description: "",
      severity: null,
      diagnosed_date: null,
      is_active: true,
    });
    setDiagnosedDate("");
    onCancel?.();
  };

  return (
    <div className={className}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-2">
          <Label htmlFor="condition-name">
            Condition Name <span className="text-red-500">*</span>
          </Label>
          <Input
            id="condition-name"
            placeholder="e.g., Diabetes Type 2, Hypertension"
            value={formData.name}
            onChange={(e) => setFormData((prev: ConditionCreate) => ({ ...prev, name: e.target.value }))}
            required
            aria-describedby="condition-name-help"
          />
          <p id="condition-name-help" className="text-xs text-gray-600">
            Enter the official name of your medical condition
          </p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            placeholder="Additional details about this condition..."
            value={formData.description || ""}
            onChange={(e) => setFormData((prev: ConditionCreate) => ({ ...prev, description: e.target.value || null }))}
            rows={3}
            aria-describedby="description-help"
          />
          <p id="description-help" className="text-xs text-gray-600">
            Optional: Add any additional details or notes about this condition
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="severity">Severity</Label>
            <Select 
              value={formData.severity || ""} 
              onValueChange={(value) => setFormData((prev: ConditionCreate) => ({ 
                ...prev, 
                severity: value === "" ? null : value as "mild" | "moderate" | "severe"
              }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Not specified</SelectItem>
                <SelectItem value="mild">Mild</SelectItem>
                <SelectItem value="moderate">Moderate</SelectItem>
                <SelectItem value="severe">Severe</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="diagnosed-date">Diagnosed Date</Label>
            <Input
              id="diagnosed-date"
              type="date"
              value={diagnosedDate}
              onChange={(e) => setDiagnosedDate(e.target.value)}
              aria-describedby="diagnosed-date-help"
            />
            <p id="diagnosed-date-help" className="text-xs text-gray-600">
              Optional: When was this condition diagnosed?
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => setFormData((prev: ConditionCreate) => ({ ...prev, is_active: e.target.checked }))}
            className="h-4 w-4 rounded border-gray-300"
          />
          <Label htmlFor="is_active" className="text-sm">
            This condition is currently active
          </Label>
        </div>

        <div className="flex gap-4 pt-4">
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !formData.name.trim()}>
            {loading ? "Adding..." : "Add Condition"}
          </Button>
        </div>
      </form>
    </div>
  );
}