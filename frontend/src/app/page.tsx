import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to the dashboard (or landing for unauthenticated users)
  redirect("/dashboard");
}