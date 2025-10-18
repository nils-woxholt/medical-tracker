"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, Pill, Stethoscope, Calendar, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { components } from "@contracts/types/api";
import { medicationLoggingApi, symptomLoggingApi } from "@/lib/api/logging";

// Type definitions from generated API schema
type MedicationLogResponse = components["schemas"]["MedicationLogResponse"];
type SymptomLogResponse = components["schemas"]["SymptomLogResponse"];

interface SummariesProps {
  className?: string;
}

const SEVERITY_COLORS = {
  none: "bg-gray-100 text-gray-800",
  mild: "bg-green-100 text-green-800",
  moderate: "bg-yellow-100 text-yellow-800",
  severe: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export function Summaries({ className }: SummariesProps) {
  const [medicationLogs, setMedicationLogs] = useState<MedicationLogResponse[]>([]);
  const [symptomLogs, setSymptomLogs] = useState<SymptomLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummaries = async () => {
      try {
        setLoading(true);
        setError(null);

        // Use the API client for type-safe requests
        const [medications, symptoms] = await Promise.allSettled([
          medicationLoggingApi.list({ limit: 5 }),
          symptomLoggingApi.list({ limit: 5 }),
        ]);

        // Handle medication logs result
        if (medications.status === 'fulfilled') {
          setMedicationLogs(medications.value);
        } else {
          console.error("Failed to fetch medication logs:", medications.reason);
        }

        // Handle symptom logs result
        if (symptoms.status === 'fulfilled') {
          setSymptomLogs(symptoms.value);
        } else {
          console.error("Failed to fetch symptom logs:", symptoms.reason);
        }

        // Only set error if both requests failed
        if (medications.status === 'rejected' && symptoms.status === 'rejected') {
          setError("Failed to load recent logs");
        }
      } catch (err) {
        console.error("Error fetching summaries:", err);
        setError(err instanceof Error ? err.message : "Failed to load summaries");
      } finally {
        setLoading(false);
      }
    };

    fetchSummaries();
  }, []);

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
  };

  const formatEffectiveness = (rating: number | null | undefined) => {
    if (!rating) return null;
    
    const labels = {
      1: "Not effective",
      2: "Slightly effective", 
      3: "Moderately effective",
      4: "Very effective",
      5: "Extremely effective",
    };
    
    return labels[rating as keyof typeof labels] || `${rating}/5`;
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Medications */}
        <Card data-testid="medication-logs-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Pill className="h-5 w-5" />
              Recent Medications
            </CardTitle>
          </CardHeader>
          <CardContent>
            {medicationLogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Pill className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No medications logged yet</p>
                <p className="text-sm">Use the form above to log your first medication</p>
              </div>
            ) : (
              <div className="space-y-4">
                {medicationLogs.map((log) => {
                  const { date, time } = formatDateTime(log.taken_at);
                  return (
                    <div key={log.id} className="border-l-2 border-blue-200 pl-4 py-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{log.medication_name}</h4>
                          <p className="text-sm text-muted-foreground">{log.dosage}</p>
                          
                          {log.effectiveness_rating && (
                            <div className="mt-2">
                              <Badge variant="outline" className="text-xs">
                                {formatEffectiveness(log.effectiveness_rating)}
                              </Badge>
                            </div>
                          )}
                          
                          {log.side_effects && (
                            <div className="mt-2">
                              <p className="text-sm text-amber-700">
                                Side effects: {log.side_effects}
                              </p>
                              {log.side_effect_severity && (
                                <Badge 
                                  className={`text-xs mt-1 ${SEVERITY_COLORS[log.side_effect_severity]}`}
                                  variant="outline"
                                >
                                  {log.side_effect_severity}
                                </Badge>
                              )}
                            </div>
                          )}
                          
                          {log.notes && (
                            <p className="text-sm text-muted-foreground mt-2">
                              {log.notes}
                            </p>
                          )}
                        </div>
                        
                        <div className="text-right text-sm text-muted-foreground ml-4">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{date}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{time}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Symptoms */}
        <Card data-testid="symptom-logs-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Stethoscope className="h-5 w-5" />
              Recent Symptoms
            </CardTitle>
          </CardHeader>
          <CardContent>
            {symptomLogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Stethoscope className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No symptoms logged yet</p>
                <p className="text-sm">Use the form above to log your first symptom</p>
              </div>
            ) : (
              <div className="space-y-4">
                {symptomLogs.map((log) => {
                  const { date, time } = formatDateTime(log.started_at);
                  return (
                    <div key={log.id} className="border-l-2 border-red-200 pl-4 py-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{log.symptom_name}</h4>
                            <Badge 
                              className={`text-xs ${SEVERITY_COLORS[log.severity]}`}
                              variant="outline"
                            >
                              {log.severity}
                            </Badge>
                          </div>
                          
                          {log.location && (
                            <p className="text-sm text-muted-foreground">
                              Location: {log.location}
                            </p>
                          )}
                          
                          {log.duration_minutes && (
                            <p className="text-sm text-muted-foreground">
                              Duration: {log.duration_minutes} minutes
                            </p>
                          )}
                          
                          {log.triggers && (
                            <p className="text-sm text-blue-700 mt-2">
                              Triggers: {log.triggers}
                            </p>
                          )}
                          
                          {log.notes && (
                            <p className="text-sm text-muted-foreground mt-2">
                              {log.notes}
                            </p>
                          )}
                        </div>
                        
                        <div className="text-right text-sm text-muted-foreground ml-4">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{date}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{time}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}