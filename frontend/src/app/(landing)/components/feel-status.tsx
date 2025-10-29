"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Smile, 
  Frown, 
  Meh, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Heart,
  Activity,
  AlertCircle,
  RefreshCw
} from "lucide-react";
import { components } from "@contracts/types/api";
import { ApiClient } from "@/lib/api/client";

// Type definitions from generated API schema - feel endpoint types will be added
interface FeelComparisonResponse {
  feel_vs_yesterday: "better" | "worse" | "same";
  confidence_score?: number;
  summary?: string;
}

interface FeelStatusProps {
  className?: string;
}

const FEEL_STATES = {
  better: {
    icon: Smile,
    color: "text-green-600",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    label: "Feeling Better",
    emoji: "😊"
  },
  worse: {
    icon: Frown,
    color: "text-red-600", 
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    label: "Feeling Worse",
    emoji: "😟"
  },
  same: {
    icon: Meh,
    color: "text-gray-600",
    bgColor: "bg-gray-50", 
    borderColor: "border-gray-200",
    label: "Feeling Same",
    emoji: "😐"
  }
};

const TREND_ICONS = {
  better: TrendingUp,
  worse: TrendingDown,
  same: Minus,
};

export function FeelStatus({ className }: FeelStatusProps) {
  const [feelData, setFeelData] = useState<FeelComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchFeelStatus = async () => {
    try {
      setLoading(true);
      setError(null);

  const client = new ApiClient();
  const data = await client.getFeelVsYesterday();
      setFeelData(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Error fetching feel status:", err);
      
      if (err instanceof Error) {
        if (err.message.includes('404')) {
          setError("Not enough data yet - log some medications and symptoms first");
        } else if (err.message.includes('401')) {
          setError("Authentication required");
        } else {
          setError(err.message);
        }
      } else {
        setError("Failed to load feel status");
      }
      setFeelData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeelStatus();
  }, []);

  const renderFeelIndicator = () => {
    if (!feelData) return null;

    const state = FEEL_STATES[feelData.feel_vs_yesterday];
    const TrendIcon = TREND_ICONS[feelData.feel_vs_yesterday];
    const StateIcon = state.icon;

    return (
      <div 
        className={`rounded-lg border-2 ${state.borderColor} ${state.bgColor} p-6`}
        role="region"
        aria-labelledby="feel-status-heading"
        aria-describedby="feel-status-description"
      >
        <div className="flex items-center justify-center mb-4">
          <div className={`rounded-full p-4 bg-white shadow-sm ${state.borderColor} border`}>
            <StateIcon 
              className={`h-12 w-12 ${state.color}`} 
              aria-hidden="true"
            />
          </div>
        </div>
        
        <div className="text-center">
          <h3 
            id="feel-status-heading"
            data-testid="feel-status-value"
            className={`text-xl font-semibold ${state.color} mb-2`}
          >
            {state.label}
          </h3>
          
          <div className="flex items-center justify-center gap-2 mb-3">
            <TrendIcon 
              className={`h-5 w-5 ${state.color}`} 
              aria-hidden="true"
            />
            <span className="text-lg" role="img" aria-label={`Feeling ${feelData.feel_vs_yesterday}`}>
              {state.emoji}
            </span>
            <span className={`text-sm font-medium ${state.color}`}>
              vs Yesterday
            </span>
          </div>

          {feelData.confidence_score && (
            <div className="mb-3">
              <Badge 
                variant="outline" 
                className="text-xs"
                aria-label={`Confidence level: ${Math.round(feelData.confidence_score * 100)} percent`}
              >
                {Math.round(feelData.confidence_score * 100)}% confidence
              </Badge>
            </div>
          )}

          {feelData.summary && (
            <p 
              id="feel-status-description"
              className="text-sm text-gray-700 mt-3 italic"
              role="note"
            >
              "{feelData.summary}"
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderEmptyState = () => (
    <div className="text-center py-12" role="region" aria-labelledby="empty-state-heading">
      <div className="relative mb-6">
        <Heart className="h-16 w-16 mx-auto text-gray-300" aria-hidden="true" />
        <Activity className="h-8 w-8 absolute -bottom-1 -right-2 text-gray-400" aria-hidden="true" />
      </div>
      
      <h3 id="empty-state-heading" className="text-lg font-medium text-gray-900 mb-2" data-testid="feel-status-value">
        Unknown
      </h3>
      
      <p className="text-gray-600 mb-4">
        Start logging your medications and symptoms to get personalized insights about how you're feeling.
      </p>
      
      <p className="text-sm text-gray-500">
        We'll analyze your recent entries to show if you're feeling better, worse, or the same compared to yesterday.
      </p>
    </div>
  );

  return (
    <Card className={className} data-testid="feel-status">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="h-5 w-5 text-red-500" aria-hidden="true" />
            How Are You Feeling?
          </div>
          
          {feelData && (
            <Button
              variant="outline"
              size="sm"
              onClick={fetchFeelStatus}
              disabled={loading}
              className="flex items-center gap-2"
              aria-label="Refresh feel status data"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
              Refresh
            </Button>
          )}
        </CardTitle>
        
        {lastUpdated && (
          <p className="text-sm text-muted-foreground">
            Last updated: <time dateTime={lastUpdated.toISOString()}>{lastUpdated.toLocaleString()}</time>
          </p>
        )}
      </CardHeader>
      
      <CardContent>
        {/* Accessibility: Live region for dynamic status updates */}
        <div 
          aria-live="polite" 
          aria-atomic="true" 
          className="sr-only"
        >
          {loading && "Loading feel status..."}
          {error && `Error loading feel status: ${error}`}
          {feelData && `Feel status updated: ${FEEL_STATES[feelData.feel_vs_yesterday].label}`}
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4" role="alert">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && !feelData && (
          <div className="flex items-center justify-center py-12" role="status" aria-label="Loading feel status">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" aria-hidden="true" />
              <p className="text-gray-600">Analyzing your health data...</p>
            </div>
          </div>
        )}

        {!loading && !error && !feelData && renderEmptyState()}
        
        {feelData && renderFeelIndicator()}
        
        {feelData && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center justify-center gap-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4" aria-hidden="true" />
                <span>Based on recent logs</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Heart className="h-4 w-4 text-red-400" aria-hidden="true" />
                <span>Updated daily</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}