"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Plus, 
  Search, 
  User, 
  Phone, 
  Mail, 
  MapPin, 
  Building, 
  Stethoscope,
  Edit,
  MoreVertical,
  Filter
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Types from our generated API types
import type { components } from "@/../contracts/types/api";

type DoctorResponse = components["schemas"]["DoctorResponse"];

interface DoctorsPageState {
  doctors: DoctorResponse[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  specialtyFilter: string;
  activeFilter: string;
}

export default function DoctorsPage() {
  const [state, setState] = useState<DoctorsPageState>({
    doctors: [],
    loading: true,
    error: null,
    searchTerm: "",
    specialtyFilter: "all",
    activeFilter: "all"
  });

  // Mock data for development - in real app this would come from API
  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock doctors data
        const mockDoctors: DoctorResponse[] = [
          {
            id: "doctor-1",
            name: "Dr. Jane Smith",
            specialty: "Endocrinology",
            phone: "+1-555-123-4567",
            email: "dr.smith@clinic.com",
            address: "123 Medical Center Drive, Suite 456",
            notes: "Highly recommended for diabetes management. Board certified with 15+ years experience.",
            is_active: true,
            created_at: "2023-01-15T10:00:00Z",
            updated_at: "2023-01-16T15:30:00Z"
          },
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
            notes: "Primary care physician with focus on preventive medicine",
            is_active: true,
            created_at: "2023-02-01T11:30:00Z",
            updated_at: null
          },
          {
            id: "doctor-4",
            name: "Dr. Robert Chen",
            specialty: "Dermatology",
            phone: "+1-555-444-7890",
            email: "r.chen@skincare.medical",
            address: "321 Wellness Center, 2nd Floor",
            notes: "Specialist in skin cancer prevention and treatment",
            is_active: false,
            created_at: "2022-08-15T09:00:00Z",
            updated_at: "2023-03-01T14:20:00Z"
          },
          {
            id: "doctor-5",
            name: "Dr. Lisa Thompson",
            specialty: "Orthopedics",
            phone: "+1-555-333-2468",
            email: "l.thompson@boneclinic.org",
            address: "567 Sports Medicine Institute",
            notes: "Sports medicine and joint replacement specialist",
            is_active: true,
            created_at: "2023-03-10T16:45:00Z",
            updated_at: null
          }
        ];
        
        setState(prev => ({
          ...prev,
          doctors: mockDoctors,
          loading: false,
          error: null
        }));
      } catch (error) {
        setState(prev => ({
          ...prev,
          doctors: [],
          loading: false,
          error: error instanceof Error ? error.message : "Failed to load doctors"
        }));
      }
    };

    fetchDoctors();
  }, []);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Not specified";
    return new Date(dateString).toLocaleDateString();
  };

  const getUniqueSpecialties = () => {
    const specialties = state.doctors
      .map(doctor => doctor.specialty)
      .filter((specialty): specialty is string => specialty !== null && specialty !== undefined);
    return [...new Set(specialties)];
  };

  const filteredDoctors = state.doctors.filter(doctor => {
    const matchesSearch = state.searchTerm === "" || 
      doctor.name.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
      (doctor.specialty && doctor.specialty.toLowerCase().includes(state.searchTerm.toLowerCase()));
    
    const matchesSpecialty = state.specialtyFilter === "all" || 
      doctor.specialty === state.specialtyFilter;
    
    const matchesActive = state.activeFilter === "all" ||
      (state.activeFilter === "active" && doctor.is_active) ||
      (state.activeFilter === "inactive" && !doctor.is_active);

    return matchesSearch && matchesSpecialty && matchesActive;
  });

  if (state.loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Doctors</h1>
          <p className="text-gray-600">Manage your healthcare providers</p>
        </div>
        
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-16 w-full" />
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
          <h1 className="text-2xl font-bold text-gray-900">Doctors</h1>
          <p className="text-gray-600">Manage your healthcare providers</p>
        </div>
        
        <Alert>
          <User className="h-4 w-4" />
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Doctors</h1>
          <p className="text-gray-600">Manage your healthcare providers</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Doctor
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="md:col-span-2">
              <Label htmlFor="search">Search doctors</Label>
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search by name or specialty..."
                  value={state.searchTerm}
                  onChange={(e) => setState(prev => ({ ...prev, searchTerm: e.target.value }))}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="specialty">Specialty</Label>
              <Select 
                value={state.specialtyFilter} 
                onValueChange={(value) => setState(prev => ({ ...prev, specialtyFilter: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All specialties" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All specialties</SelectItem>
                  {getUniqueSpecialties().map((specialty) => (
                    <SelectItem key={specialty} value={specialty}>
                      {specialty}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="status">Status</Label>
              <Select 
                value={state.activeFilter} 
                onValueChange={(value) => setState(prev => ({ ...prev, activeFilter: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All doctors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All doctors</SelectItem>
                  <SelectItem value="active">Active only</SelectItem>
                  <SelectItem value="inactive">Inactive only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Showing {filteredDoctors.length} of {state.doctors.length} doctors
        </p>
        {(state.searchTerm || state.specialtyFilter !== "all" || state.activeFilter !== "all") && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setState(prev => ({ 
              ...prev, 
              searchTerm: "", 
              specialtyFilter: "all", 
              activeFilter: "all" 
            }))}
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Doctors List */}
      {filteredDoctors.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <User className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {state.doctors.length === 0 ? "No doctors yet" : "No doctors match your filters"}
            </h3>
            <p className="text-gray-600 text-center mb-6">
              {state.doctors.length === 0 
                ? "Add your first healthcare provider to get started."
                : "Try adjusting your search or filters to find doctors."
              }
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Doctor
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredDoctors.map((doctor) => (
            <Card key={doctor.id} className="overflow-hidden">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="bg-blue-100 p-3 rounded-full">
                      <Stethoscope className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {doctor.name}
                        <Badge variant={doctor.is_active ? "default" : "secondary"}>
                          {doctor.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {doctor.specialty || "General Practice"}
                      </CardDescription>
                    </div>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit doctor
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Building className="h-4 w-4 mr-2" />
                        View conditions
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">
                        {doctor.is_active ? "Deactivate" : "Activate"}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Contact Information</h4>
                    
                    {doctor.phone && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Phone className="h-4 w-4 mr-3 text-gray-400" />
                        <span>{doctor.phone}</span>
                      </div>
                    )}
                    
                    {doctor.email && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Mail className="h-4 w-4 mr-3 text-gray-400" />
                        <a 
                          href={`mailto:${doctor.email}`} 
                          className="text-blue-600 hover:underline"
                        >
                          {doctor.email}
                        </a>
                      </div>
                    )}
                    
                    {doctor.address && (
                      <div className="flex items-start text-sm text-gray-600">
                        <MapPin className="h-4 w-4 mr-3 mt-0.5 text-gray-400 flex-shrink-0" />
                        <span>{doctor.address}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Additional Information</h4>
                    
                    <div className="flex items-center text-sm text-gray-600">
                      <User className="h-4 w-4 mr-3 text-gray-400" />
                      <span>Added {formatDate(doctor.created_at)}</span>
                    </div>
                    
                    {doctor.updated_at && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Edit className="h-4 w-4 mr-3 text-gray-400" />
                        <span>Updated {formatDate(doctor.updated_at)}</span>
                      </div>
                    )}
                    
                    {doctor.notes && (
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-900">
                          <Building className="h-4 w-4 inline mr-2" />
                          {doctor.notes}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}