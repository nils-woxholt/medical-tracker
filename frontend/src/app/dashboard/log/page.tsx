import { LogForms } from "../../(landing)/components/log-forms";

export default function LogPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Log Entry</h1>
        <p className="text-gray-600">Record your medications and symptoms.</p>
      </div>

      <LogForms />
    </div>
  );
}