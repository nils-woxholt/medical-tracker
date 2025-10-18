"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, Pill, Stethoscope, Plus, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { components } from "@contracts/types/api";
import { medicationLoggingApi, symptomLoggingApi, OptimisticUpdates } from "@/lib/api/logging";

// Type definitions from generated API schema
type MedicationLogCreate = components["schemas"]["MedicationLogCreate"];
type SymptomLogCreate = components["schemas"]["SymptomLogCreate"];
type SeverityLevel = components["schemas"]["SeverityLevel"];

const SEVERITY_LEVELS: { value: SeverityLevel; label: string; color: string }[] = [
  { value: "none", label: "None", color: "bg-gray-100" },
  { value: "mild", label: "Mild", color: "bg-green-100" },
  { value: "moderate", label: "Moderate", color: "bg-yellow-100" },
  { value: "severe", label: "Severe", color: "bg-orange-100" },
  { value: "critical", label: "Critical", color: "bg-red-100" },
];

const EFFECTIVENESS_RATINGS = [
  { value: 1, label: "Not effective" },
  { value: 2, label: "Slightly effective" },
  { value: 3, label: "Moderately effective" },
  { value: 4, label: "Very effective" },
  { value: 5, label: "Extremely effective" },
];

export function LogForms() {
  const [medicationData, setMedicationData] = useState<Partial<MedicationLogCreate>>({
    taken_at: new Date().toISOString().slice(0, 16), // Default to current datetime
  });
  
  const [symptomData, setSymptomData] = useState<Partial<SymptomLogCreate>>({
    started_at: new Date().toISOString().slice(0, 16), // Default to current datetime
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleMedicationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate required fields
      if (!medicationData.medication_name || !medicationData.dosage || !medicationData.taken_at) {
        throw new Error("Please fill in all required fields");
      }

      const payload: MedicationLogCreate = {
        medication_name: medicationData.medication_name,
        dosage: medicationData.dosage,
        taken_at: medicationData.taken_at,
        notes: medicationData.notes || null,
        side_effects: medicationData.side_effects || null,
        side_effect_severity: medicationData.side_effect_severity || null,
        effectiveness_rating: medicationData.effectiveness_rating || null,
      };

      // Create optimistic update for immediate UI feedback
      const optimisticLog = OptimisticUpdates.createOptimisticMedicationLog(payload);
      
      // TODO: Update parent component state optimistically here
      // For now, we'll just show success immediately then call the API
      
      // Call the API
      await medicationLoggingApi.create(payload);

      setSuccess("Medication logged successfully!");
      setMedicationData({
        taken_at: new Date().toISOString().slice(0, 16),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSymptomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate required fields
      if (!symptomData.symptom_name || !symptomData.severity || !symptomData.started_at) {
        throw new Error("Please fill in all required fields");
      }

      const payload: SymptomLogCreate = {
        symptom_name: symptomData.symptom_name,
        severity: symptomData.severity,
        started_at: symptomData.started_at,
        ended_at: symptomData.ended_at || null,
        duration_minutes: symptomData.duration_minutes || null,
        triggers: symptomData.triggers || null,
        location: symptomData.location || null,
        notes: symptomData.notes || null,
      };

      // Create optimistic update for immediate UI feedback
      const optimisticLog = OptimisticUpdates.createOptimisticSymptomLog(payload);
      
      // TODO: Update parent component state optimistically here
      // For now, we'll just show success immediately then call the API
      
      // Call the API
      await symptomLoggingApi.create(payload);

      setSuccess("Symptom logged successfully!");
      setSymptomData({
        started_at: new Date().toISOString().slice(0, 16),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Log Your Health Data
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <AlertCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-700">{success}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="medication" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="medication" className="flex items-center gap-2">
              <Pill className="h-4 w-4" />
              Medication
            </TabsTrigger>
            <TabsTrigger value="symptom" className="flex items-center gap-2">
              <Stethoscope className="h-4 w-4" />
              Symptom
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="medication" className="space-y-4">
            <form onSubmit={handleMedicationSubmit} className="space-y-4" data-testid="medication-log-form">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="medication-name">Medication Name *</Label>
                  <Input
                    id="medication-name"
                    data-testid="medication-name-input"
                    value={medicationData.medication_name || ""}
                    onChange={(e) => setMedicationData({ ...medicationData, medication_name: e.target.value })}
                    placeholder="e.g., Ibuprofen"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="dosage">Dosage *</Label>
                  <Input
                    id="dosage"
                    data-testid="dosage-input"
                    value={medicationData.dosage || ""}
                    onChange={(e) => setMedicationData({ ...medicationData, dosage: e.target.value })}
                    placeholder="e.g., 200mg, 2 tablets"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="taken-at" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Taken At *
                </Label>
                <Input
                  id="taken-at"
                  data-testid="taken-at-input"
                  type="datetime-local"
                  value={medicationData.taken_at || ""}
                  onChange={(e) => setMedicationData({ ...medicationData, taken_at: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="effectiveness">Effectiveness Rating</Label>
                <Select
                  value={medicationData.effectiveness_rating?.toString() || ""}
                  onValueChange={(value) => setMedicationData({ 
                    ...medicationData, 
                    effectiveness_rating: value ? parseInt(value) : null 
                  })}
                >
                  <SelectTrigger data-testid="effectiveness-rating-select">
                    <SelectValue placeholder="How effective was this medication?" />
                  </SelectTrigger>
                  <SelectContent>
                    {EFFECTIVENESS_RATINGS.map((rating) => (
                      <SelectItem key={rating.value} value={rating.value.toString()}>
                        {rating.value} - {rating.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="side-effects">Side Effects</Label>
                <Textarea
                  id="side-effects"
                  data-testid="side-effects-textarea"
                  value={medicationData.side_effects || ""}
                  onChange={(e) => setMedicationData({ ...medicationData, side_effects: e.target.value })}
                  placeholder="Describe any side effects experienced..."
                  rows={3}
                />
              </div>

              {medicationData.side_effects && (
                <div className="space-y-2">
                  <Label>Side Effect Severity</Label>
                  <Select
                    value={medicationData.side_effect_severity || ""}
                    onValueChange={(value) => setMedicationData({ 
                      ...medicationData, 
                      side_effect_severity: value as SeverityLevel 
                    })}
                  >
                    <SelectTrigger data-testid="side-effect-select">
                      <SelectValue placeholder="Select severity level" />
                    </SelectTrigger>
                    <SelectContent>
                      {SEVERITY_LEVELS.map((severity) => (
                        <SelectItem key={severity.value} value={severity.value}>
                          <div className="flex items-center gap-2">
                            <Badge className={severity.color}>{severity.label}</Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="medication-notes">Notes</Label>
                <Textarea
                  id="medication-notes"
                  data-testid="notes-textarea"
                  value={medicationData.notes || ""}
                  onChange={(e) => setMedicationData({ ...medicationData, notes: e.target.value })}
                  placeholder="Additional notes about this medication..."
                  rows={3}
                />
              </div>

              <Button type="submit" disabled={isSubmitting} className="w-full" data-testid="submit-button">
                {isSubmitting ? "Logging..." : "Log Medication"}
              </Button>
            </form>
          </TabsContent>
          
          <TabsContent value="symptom" className="space-y-4">
            <form onSubmit={handleSymptomSubmit} className="space-y-4" data-testid="symptom-log-form">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="symptom-name">Symptom Name *</Label>
                  <Input
                    id="symptom-name"
                    data-testid="symptom-name-input"
                    value={symptomData.symptom_name || ""}
                    onChange={(e) => setSymptomData({ ...symptomData, symptom_name: e.target.value })}
                    placeholder="e.g., Headache, Nausea"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Severity *</Label>
                  <Select
                    value={symptomData.severity || ""}
                    onValueChange={(value) => setSymptomData({ 
                      ...symptomData, 
                      severity: value as SeverityLevel 
                    })}
                  >
                    <SelectTrigger data-testid="severity-select">
                      <SelectValue placeholder="Select severity level" />
                    </SelectTrigger>
                    <SelectContent>
                      {SEVERITY_LEVELS.map((severity) => (
                        <SelectItem key={severity.value} value={severity.value}>
                          <div className="flex items-center gap-2">
                            <Badge className={severity.color}>{severity.label}</Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="started-at" className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Started At *
                  </Label>
                  <Input
                    id="started-at"
                    data-testid="started-at-input"
                    type="datetime-local"
                    value={symptomData.started_at || ""}
                    onChange={(e) => setSymptomData({ ...symptomData, started_at: e.target.value })}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="ended-at">Ended At</Label>
                  <Input
                    id="ended-at"
                    data-testid="ended-at-input"
                    type="datetime-local"
                    value={symptomData.ended_at || ""}
                    onChange={(e) => setSymptomData({ ...symptomData, ended_at: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="duration">Duration (minutes)</Label>
                  <Input
                    id="duration"
                    data-testid="duration-input"
                    type="number"
                    value={symptomData.duration_minutes || ""}
                    onChange={(e) => setSymptomData({ 
                      ...symptomData, 
                      duration_minutes: e.target.value ? parseInt(e.target.value) : null 
                    })}
                    placeholder="e.g., 30"
                    min="0"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    data-testid="location-input"
                    value={symptomData.location || ""}
                    onChange={(e) => setSymptomData({ ...symptomData, location: e.target.value })}
                    placeholder="e.g., Left temple, Upper abdomen"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="impact-rating">Impact Rating</Label>
                <Select
                  value={symptomData.impact_rating?.toString() || ""}
                  onValueChange={(value) => setSymptomData({ 
                    ...symptomData, 
                    impact_rating: value ? parseInt(value) : null 
                  })}
                >
                  <SelectTrigger data-testid="impact-rating-select">
                    <SelectValue placeholder="How much did this impact your day?" />
                  </SelectTrigger>
                  <SelectContent>
                    {EFFECTIVENESS_RATINGS.map((rating) => (
                      <SelectItem key={rating.value} value={rating.value.toString()}>
                        {rating.value}/5 - {rating.label.replace('effective', 'impactful')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="triggers">Potential Triggers</Label>
                <Textarea
                  id="triggers"
                  data-testid="triggers-input"
                  value={symptomData.triggers || ""}
                  onChange={(e) => setSymptomData({ ...symptomData, triggers: e.target.value })}
                  placeholder="What might have caused this symptom? (stress, food, weather, etc.)"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="symptom-notes">Notes</Label>
                <Textarea
                  id="symptom-notes"
                  data-testid="notes-textarea"
                  value={symptomData.notes || ""}
                  onChange={(e) => setSymptomData({ ...symptomData, notes: e.target.value })}
                  placeholder="Additional notes about this symptom..."
                  rows={3}
                />
              </div>

              <Button type="submit" disabled={isSubmitting} className="w-full" data-testid="submit-button">
                {isSubmitting ? "Logging..." : "Log Symptom"}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}