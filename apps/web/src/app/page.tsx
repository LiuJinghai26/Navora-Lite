import { redirect } from "next/navigation";

export default function Home() {
  // New Chat is the primary entry point for the app.
  redirect("/new-chat");
}
