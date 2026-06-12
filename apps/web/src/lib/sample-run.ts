import type { Run } from "./types";

const now = new Date("2026-06-12T06:10:50.000Z").toISOString();

export const sampleRun: Run = {
  id: "demo",
  title: "Add Product and Extract Quantity",
  task: "Please add FIRESTONE W01-377-8537 to the cart with quantity 1 and extract the quantity.",
  url: "http://localhost:8000/mock/findparts",
  status: "completed",
  controlStatus: "completed",
  startedAt: now,
  finishedAt: new Date("2026-06-12T06:13:16.000Z").toISOString(),
  durationMs: 146000,
  messages: [
    {
      id: "msg_demo_user",
      role: "user",
      content: "Please add FIRESTONE W01-377-8537 to the cart with quantity 1 and extract the quantity.",
      createdAt: now
    },
    {
      id: "msg_demo_agent",
      role: "assistant",
      content:
        "On it. I will search for the product, add it to the cart with quantity 1, then extract the quantity from your cart.",
      createdAt: new Date("2026-06-12T06:10:53.000Z").toISOString(),
      checklist: [
        { text: 'Searching for product "FIRESTONE W01-377-8537"', status: "success" },
        { text: "Added product to cart with quantity 1", status: "success" },
        { text: "Open cart page and locate item", status: "success" },
        { text: "Extract quantity from cart", status: "success" }
      ]
    },
    {
      id: "msg_demo_done",
      role: "assistant",
      content: "Done. The product has been added and the quantity is 1.",
      createdAt: new Date("2026-06-12T06:13:16.000Z").toISOString()
    }
  ],
  timeline: [
    {
      id: "step_1",
      index: 1,
      action: "goto",
      description: "Navigate to FindItParts",
      status: "success",
      startedAt: new Date("2026-06-12T06:10:52.000Z").toISOString(),
      durationMs: 1800
    },
    {
      id: "step_2",
      index: 2,
      action: "fill",
      description: 'Search for "FIRESTONE W01-377-8537"',
      status: "success",
      startedAt: new Date("2026-06-12T06:10:58.000Z").toISOString(),
      durationMs: 6200
    },
    {
      id: "step_3",
      index: 3,
      action: "click",
      description: "Open product page",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:05.000Z").toISOString(),
      durationMs: 4100
    },
    {
      id: "step_4",
      index: 4,
      action: "fill",
      description: "Set quantity to 1",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:12.000Z").toISOString(),
      durationMs: 2300
    },
    {
      id: "step_5",
      index: 5,
      action: "click",
      description: "Add product to cart",
      status: "success",
      startedAt: new Date("2026-06-12T06:11:22.000Z").toISOString(),
      durationMs: 3700
    },
    {
      id: "step_6",
      index: 6,
      action: "extract",
      description: "Extract quantity from cart",
      status: "success",
      startedAt: new Date("2026-06-12T06:12:18.000Z").toISOString(),
      durationMs: 46700
    }
  ],
  screenshots: [
    {
      id: "shot_demo",
      title: "Browser preview",
      imageUrl: "/assets/browser-preview-placeholder.png",
      createdAt: now
    }
  ],
  extracted: {
    product_name: "FIRESTONE W01-377-8537",
    quantity: 1
  },
  inputs: {
    task: "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1",
    url: "http://localhost:8000/mock/findparts",
    model: "qwen3",
    browser: "chromium"
  }
};

