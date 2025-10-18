"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Calendar, User, Phone, Mail, MapPin, Building, Activity } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Types from our generated API types
import type { components } from "@/../contracts/types/api";

type PassportResponse = components["schemas"]["PassportResponse"];
type PassportItem = components["schemas"]["PassportItem"];
type ConditionResponse = components["schemas"]["ConditionResponse"];
type DoctorResponse = components["schemas"]["DoctorResponse"];

interface PassportPageState {
  passport: PassportResponse | null;
  loading: boolean;
  error: string | null;
}

export default function PassportPage() {
  const [state, setState] = useState<PassportPageState>({
    passport: null,
    loading: true,
    error: null,
  });

  // Mock data for development - in real app this would come from API
  useEffect(() => {
    const fetchPassport = async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock passport data
        const mockPassport: PassportResponse = {
          items: [
            {
              condition: {
                id: "condition-1",
                name: "Diabetes Type 2",
                description: "Adult-onset diabetes mellitus",
                severity: "moderate",
                diagnosed_date: "2023-01-15",
                is_active: true,
                created_at: "2023-01-15T10:00:00Z",
                updated_at: "2023-01-16T15:30:00Z"
              },
              doctors: [
                {
                  id: "doctor-1",
                  name: "Dr. Jane Smith",
                  specialty: "Endocrinology",
                  phone: "+1-555-123-4567",
                  email: "dr.smith@clinic.com",
                  address: "123 Medical Center Drive, Suite 456",
                  notes: "Highly recommended for diabetes management",
                  is_active: true,
                  created_at: "2023-01-15T10:00:00Z",
                  updated_at: null
                }
              ]
            },
            {
              condition: {
                id: "condition-2",
                name: "Hypertension",
                description: "High blood pressure requiring monitoring",
                severity: "mild",
                diagnosed_date: "2022-11-20",
                is_active: true,
                created_at: "2022-11-20T14:00:00Z",
                updated_at: null
              },
              doctors: [
                {
                  id: "doctor-2",
                  name: "Dr. Michael Johnson",
                  specialty: "Cardiology",
                  phone: "+1-555-987-6543",
                  email: "m.johnson@heart.clinic",
                  address: "456 Heart Health Plaza, Floor 3",
                  notes: null,
                  is_active: true,
                  created_at: "2022-11-20T14:00:00Z",
                  updated_at: "2023-01-10T09:15:00Z"
                },
                {
                  id: "doctor-3",
                  name: "Dr. Sarah Wilson",
                  specialty: "Internal Medicine",
                  phone: "+1-555-555-1234",
                  email: "s.wilson@primarycare.com",
                  address: "789 Health Boulevard, Building A",
                  notes: "Primary care physician",
                  is_active: true,
                  created_at: "2023-02-01T11:30:00Z",
                  updated_at: null
                }
              ]
            }
          ],
          total_conditions: 2,
          total_doctors: 3,
          generated_at: new Date().toISOString()
        };
        
        setState({
          passport: mockPassport,
          loading: false,
          error: null
        });
      } catch (error) {
        setState({
          passport: null,
          loading: false,
          error: error instanceof Error ? error.message : "Failed to load passport"
        });
      }
    };

    fetchPassport();
  }, []);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Not specified";
    return new Date(dateString).toLocaleDateString();
  };

  const getSeverityColor = (severity: string | null) => {
    switch (severity) {
      case "mild": return "bg-yellow-100 text-yellow-800";
      case "moderate": return "bg-orange-100 text-orange-800";
      case "severe": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (state.loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Passport</h1>
          <p className="text-gray-600">Your comprehensive medical condition overview</p>
        </div>
        
        <div className="grid gap-6">
          {[1, 2].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Passport</h1>
          <p className="text-gray-600">Your comprehensive medical condition overview</p>
        </div>
        
        <Alert>
          <Activity className="h-4 w-4" />
          <AlertDescription>
            {state.error}
          </AlertDescription>
        </Alert>
        
        <Button onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  if (!state.passport || state.passport.items.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Passport</h1>
          <p className="text-gray-600">Your comprehensive medical condition overview</p>
        </div>
        
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No medical conditions yet</h3>
            <p className="text-gray-600 text-center mb-6">
              Start by adding your medical conditions and the doctors who treat them.
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add First Condition
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Passport</h1>
          <p className="text-gray-600">Your comprehensive medical condition overview</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Condition
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Conditions</p>
                <p className="text-2xl font-bold text-gray-900">{state.passport.total_conditions}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <User className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Doctors</p>
                <p className="text-2xl font-bold text-gray-900">{state.passport.total_doctors}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="col-span-2 md:col-span-1">
          <CardContent className="p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Updated</p>
                <p className="text-sm font-bold text-gray-900">
                  {formatDate(state.passport.generated_at)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Condition Cards */}
      <div className="space-y-6">
        {state.passport.items.map((item) => (
          <Card key={item.condition.id} className="overflow-hidden">
            <CardHeader className="bg-gray-50">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {item.condition.name}
                    {item.condition.severity && (
                      <Badge 
                        variant="secondary" 
                        className={getSeverityColor(item.condition.severity)}
                      >
                        {item.condition.severity}
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {item.condition.description || "No description provided"}
                  </CardDescription>
                </div>
                <Badge variant={item.condition.is_active ? "default" : "secondary"}>
                  {item.condition.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              
              {item.condition.diagnosed_date && (
                <div className="flex items-center text-sm text-gray-600 mt-2">
                  <Calendar className="h-4 w-4 mr-1" />
                  Diagnosed: {formatDate(item.condition.diagnosed_date)}
                </div>
              )}
            </CardHeader>
            
            <CardContent className="p-6">
              <h4 className="font-medium text-gray-900 mb-4">
                Healthcare Providers ({item.doctors.length})
              </h4>
              
              {item.doctors.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <User className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No doctors assigned to this condition</p>
                  <Button variant="outline" size="sm" className="mt-2">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Doctor
                  </Button>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {item.doctors.map((doctor) => (
                    <Card key={doctor.id} className="border border-gray-200">
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <h5 className="font-medium text-gray-900">{doctor.name}</h5>
                              {doctor.specialty && (
                                <p className="text-sm text-gray-600">{doctor.specialty}</p>
                              )}
                            </div>
                            <Badge variant={doctor.is_active ? "default" : "secondary"} className="text-xs">
                              {doctor.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </div>
                          
                          <div className="space-y-2 text-sm">
                            {doctor.phone && (
                              <div className="flex items-center text-gray-600">
                                <Phone className="h-4 w-4 mr-2" />
                                {doctor.phone}
                              </div>
                            )}
                            
                            {doctor.email && (
                              <div className="flex items-center text-gray-600">
                                <Mail className="h-4 w-4 mr-2" />
                                {doctor.email}
                              </div>
                            )}
                            
                            {doctor.address && (
                              <div className="flex items-start text-gray-600">
                                <MapPin className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                                <span className="text-xs">{doctor.address}</span>
                              </div>
                            )}
                            
                            {doctor.notes && (
                              <div className="bg-blue-50 p-2 rounded text-xs text-blue-900">
                                <Building className="h-3 w-3 inline mr-1" />
                                {doctor.notes}
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 pt-6">
        <Button variant="outline">
          Export Passport
        </Button>
        <Button variant="outline">
          Print Summary
        </Button>
      </div>
    </div>
  );
}