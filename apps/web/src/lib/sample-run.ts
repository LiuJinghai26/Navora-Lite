import type { Run } from "./types";

// Bundled demo data keeps /runs/demo useful when the backend is offline.
const start = new Date("2026-06-12T06:10:50.000Z");
const now = start.toISOString();

export const sampleRun: Run = {
  id: "demo",
  title: "Hacker News Top Story",
  task: "Open Hacker News and extract the current top story with its source, score, age, and comments.",
  url: "https://news.ycombinator.com/",
  status: "completed",
  controlStatus: "completed",
  startedAt: now,
  finishedAt: new Date("2026-06-12T06:11:12.000Z").toISOString(),
  durationMs: 22000,
  messages: [
    {
      id: "msg_demo_user",
      role: "user",
      content: "Open Hacker News and extract the current top story with its source, score, age, and comments.",
      createdAt: now
    },
    {
      id: "msg_demo_agent",
      role: "assistant",
      content: "On it. I will open Hacker News, wait for the page, and extract the requested story details.",
      createdAt: new Date("2026-06-12T06:10:53.000Z").toISOString(),
      checklist: [
        { text: "Open https://news.ycombinator.com/", status: "success" },
        { text: "Wait for Hacker News stories", status: "success" },
        { text: "Extract hacker news stories", status: "success" }
      ]
    },
    {
      id: "msg_demo_done",
      role: "assistant",
      content: "Done. The requested Hacker News story details are ready.",
      createdAt: new Date("2026-06-12T06:11:12.000Z").toISOString()
    }
  ],
  timeline: [
    {
      id: "step_1",
      index: 1,
      action: "goto",
      description: "Navigate to https://news.ycombinator.com/",
      status: "success",
      startedAt: new Date("2026-06-12T06:10:52.000Z").toISOString(),
      durationMs: 1400
    },
    {
      id: "step_2",
      index: 2,
      action: "wait",
      description: "Wait for Hacker News stories",
      status: "success",
      startedAt: new Date("2026-06-12T06:10:56.000Z").toISOString(),
      durationMs: 1000
    },
    {
      id: "step_3",
      index: 3,
      action: "extract",
      description: "Extract hacker news stories",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:00.000Z").toISOString(),
      durationMs: 4200
    }
  ],
  screenshots: [],
  extracted: {
    source: "Hacker News",
    top_story: {
      rank: 1,
      title: "Example top story",
      site: "example.com",
      points: "348 points",
      comments: "96 comments"
    }
  },
  inputs: {
    task: "Open Hacker News and extract the current top story with its source, score, age, and comments.",
    url: "https://news.ycombinator.com/",
    model: "sample",
    browser: "chromium"
  }
};
