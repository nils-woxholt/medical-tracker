import { LogForms } from "../(landing)/components/log-forms";
import { Summaries } from "../(landing)/components/summaries";
import { FeelStatus } from "../(landing)/components/feel-status";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Here's your health overview.</p>
      </div>

      <div className="grid gap-6">
        <FeelStatus className="max-w-2xl" />
        <LogForms />
        <Summaries />
      </div>
    </div>
  );
}