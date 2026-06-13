import type { Run } from "./types";

const start = new Date("2026-06-12T06:10:50.000Z");
const now = start.toISOString();

const screenshots = [
  { id: "shot_demo_01", title: "Navigate to local storefront", imageUrl: "/assets/demo-office-01-open.svg" },
  { id: "shot_demo_02", title: "Fill search input", imageUrl: "/assets/demo-office-02-search.svg" },
  { id: "shot_demo_03", title: "Submit product search", imageUrl: "/assets/demo-office-03-results.svg" },
  { id: "shot_demo_04", title: "Open product detail", imageUrl: "/assets/demo-office-04-detail.svg" },
  { id: "shot_demo_05", title: "Select Warm White color", imageUrl: "/assets/demo-office-05-color.svg" },
  { id: "shot_demo_06", title: "Set quantity to 2", imageUrl: "/assets/demo-office-06-quantity.svg" },
  { id: "shot_demo_07", title: "Add configured item to cart", imageUrl: "/assets/demo-office-07-add.svg" },
  { id: "shot_demo_08", title: "Open cart summary", imageUrl: "/assets/demo-office-08-cart.svg" },
  { id: "shot_demo_09", title: "Extract cart summary", imageUrl: "/assets/demo-office-09-extract.svg" }
].map((shot, index) => ({
  ...shot,
  createdAt: new Date(start.getTime() + (index + 1) * 5000).toISOString()
}));

export const sampleRun: Run = {
  id: "demo",
  title: "Configure Desk Lamp Cart",
  task: "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary.",
  url: "http://localhost:8000/mock/findparts",
  status: "completed",
  controlStatus: "completed",
  startedAt: now,
  finishedAt: new Date("2026-06-12T06:11:45.000Z").toISOString(),
  durationMs: 55000,
  messages: [
    {
      id: "msg_demo_user",
      role: "user",
      content: "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary.",
      createdAt: now
    },
    {
      id: "msg_demo_agent",
      role: "assistant",
      content:
        "On it. I will find the desk lamp, choose the warm white option, set quantity to 2, add it to the cart, then extract the cart summary.",
      createdAt: new Date("2026-06-12T06:10:53.000Z").toISOString(),
      checklist: [
        { text: "Open the local demo storefront", status: "success" },
        { text: 'Search for "AURORA TASK LAMP"', status: "success" },
        { text: "Open product page and locate item", status: "success" },
        { text: "Choose the requested product color", status: "success" },
        { text: "Set quantity to 2", status: "success" },
        { text: "Add the configured product to cart", status: "success" },
        { text: "Extract cart summary", status: "success" }
      ]
    },
    {
      id: "msg_demo_done",
      role: "assistant",
      content: "Done. The lamp has been configured, added to the cart, and the cart summary is ready.",
      createdAt: new Date("2026-06-12T06:11:45.000Z").toISOString()
    }
  ],
  timeline: [
    {
      id: "step_1",
      index: 1,
      action: "goto",
      description: "Navigate to local storefront",
      status: "success",
      startedAt: new Date("2026-06-12T06:10:52.000Z").toISOString(),
      durationMs: 1400,
      screenshotUrl: screenshots[0].imageUrl
    },
    {
      id: "step_2",
      index: 2,
      action: "fill",
      description: 'Search for "AURORA TASK LAMP"',
      status: "success",
      startedAt: new Date("2026-06-12T06:10:57.000Z").toISOString(),
      durationMs: 2100,
      screenshotUrl: screenshots[1].imageUrl
    },
    {
      id: "step_3",
      index: 3,
      action: "click",
      description: "Submit product search",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:02.000Z").toISOString(),
      durationMs: 2500,
      screenshotUrl: screenshots[2].imageUrl
    },
    {
      id: "step_4",
      index: 4,
      action: "click",
      description: "Open product detail",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:08.000Z").toISOString(),
      durationMs: 3200,
      screenshotUrl: screenshots[3].imageUrl
    },
    {
      id: "step_5",
      index: 5,
      action: "click",
      description: "Select Warm White color",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:15.000Z").toISOString(),
      durationMs: 1800,
      screenshotUrl: screenshots[4].imageUrl
    },
    {
      id: "step_6",
      index: 6,
      action: "fill",
      description: "Set quantity to 2",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:20.000Z").toISOString(),
      durationMs: 1900,
      screenshotUrl: screenshots[5].imageUrl
    },
    {
      id: "step_7",
      index: 7,
      action: "click",
      description: "Add configured item to cart",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:26.000Z").toISOString(),
      durationMs: 2300,
      screenshotUrl: screenshots[6].imageUrl
    },
    {
      id: "step_8",
      index: 8,
      action: "click",
      description: "Open cart summary",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:33.000Z").toISOString(),
      durationMs: 1600,
      screenshotUrl: screenshots[7].imageUrl
    },
    {
      id: "step_9",
      index: 9,
      action: "extract",
      description: "Extract cart summary",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:40.000Z").toISOString(),
      durationMs: 4200,
      screenshotUrl: screenshots[8].imageUrl
    }
  ],
  screenshots,
  extracted: {
    product_name: "AURORA TASK LAMP",
    color: "Warm White",
    quantity: 2,
    subtotal: "$178"
  },
  inputs: {
    task: "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary",
    url: "http://localhost:8000/mock/findparts",
    model: "mock planner",
    browser: "chromium or mock browser"
  }
};
