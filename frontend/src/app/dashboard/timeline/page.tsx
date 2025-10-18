import { Summaries } from "../../(landing)/components/summaries";

export default function TimelinePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Timeline</h1>
        <p className="text-gray-600">View your health history and patterns.</p>
      </div>

      <Summaries />
    </div>
  );
}