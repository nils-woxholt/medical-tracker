"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, User, Phone, Mail, MapPin, Building, Plus } from "lucide-react";

// Types from our generated API types
import type { components } from "../../../../../contracts/types/api";

type PassportItem = components["schemas"]["PassportItem"];
type ConditionResponse = components["schemas"]["ConditionResponse"];
type DoctorResponse = components["schemas"]["DoctorResponse"];

interface PassportListProps {
  items: PassportItem[];
  onAddDoctor?: (conditionId: string) => void;
  onEditCondition?: (condition: ConditionResponse) => void;
  onEditDoctor?: (doctor: DoctorResponse) => void;
  className?: string;
}

export function PassportList({ 
  items, 
  onAddDoctor, 
  onEditCondition, 
  onEditDoctor, 
  className 
}: PassportListProps) {
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

  if (items.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <User className="h-12 w-12 text-gray-400 mb-4" />
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
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {items.map((item) => (
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
              <div className="flex gap-2">
                <Badge variant={item.condition.is_active ? "default" : "secondary"}>
                  {item.condition.is_active ? "Active" : "Inactive"}
                </Badge>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => onEditCondition?.(item.condition)}
                >
                  Edit
                </Button>
              </div>
            </div>
            
            {item.condition.diagnosed_date && (
              <div className="flex items-center text-sm text-gray-600 mt-2">
                <Calendar className="h-4 w-4 mr-1" />
                Diagnosed: {formatDate(item.condition.diagnosed_date)}
              </div>
            )}
          </CardHeader>
          
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-medium text-gray-900">
                Healthcare Providers ({item.doctors.length})
              </h4>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => onAddDoctor?.(item.condition.id)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Doctor
              </Button>
            </div>
            
            {item.doctors.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <User className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No doctors assigned to this condition</p>
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
                          <div className="flex items-center gap-2">
                            <Badge variant={doctor.is_active ? "default" : "secondary"} className="text-xs">
                              {doctor.is_active ? "Active" : "Inactive"}
                            </Badge>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => onEditDoctor?.(doctor)}
                            >
                              Edit
                            </Button>
                          </div>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          {doctor.phone && (
                            <div className="flex items-center text-gray-600">
                              <Phone className="h-4 w-4 mr-2" />
                              <a href={`tel:${doctor.phone}`} className="hover:text-blue-600">
                                {doctor.phone}
                              </a>
                            </div>
                          )}
                          
                          {doctor.email && (
                            <div className="flex items-center text-gray-600">
                              <Mail className="h-4 w-4 mr-2" />
                              <a 
                                href={`mailto:${doctor.email}`} 
                                className="hover:text-blue-600"
                              >
                                {doctor.email}
                              </a>
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
  );
}