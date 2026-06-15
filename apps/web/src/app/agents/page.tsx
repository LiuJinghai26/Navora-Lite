import { redirect } from "next/navigation";

export default function AgentsPage() {
  // The current navigation keeps historical agent tasks under Tasks.
  redirect("/tasks");
}
