import { LogForms } from "./components/log-forms";
import { Summaries } from "./components/summaries";
import { FeelStatus } from "./components/feel-status";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            SaaS Medical Tracker
          </h1>
          <p className="text-lg text-gray-600">
            Track your medications, log symptoms, and manage your health data securely
          </p>
        </header>

        <main className="space-y-8">
          <FeelStatus className="max-w-2xl mx-auto" />
          <LogForms />
          <Summaries />
        </main>
      </div>
    </div>
  );
}