export interface PresetTask {
  id: string;
  title: string;
  complexity: "Simple" | "Medium" | "Complex";
  task: string;
  url: string;
  summary: string;
}

export const PRESET_TASKS: PresetTask[] = [
  {
    id: "hn-top-story",
    title: "Hacker News Top Story",
    complexity: "Simple",
    task: "Open Hacker News and extract the current top story with its source, score, age, and comments.",
    url: "https://news.ycombinator.com/",
    summary: "Open one page, wait for the feed, extract the first ranked story."
  },
  {
    id: "wikipedia-python-summary",
    title: "Wikipedia Python Summary",
    complexity: "Medium",
    task: "Open the Wikipedia Python article and extract the lead summary, infobox language details, and page metadata.",
    url: "https://en.wikipedia.org/wiki/Python_(programming_language)",
    summary: "Open a knowledge article and extract structured facts from the lead and infobox."
  },
  {
    id: "mdn-api-research",
    title: "MDN Web API Research",
    complexity: "Complex",
    task: "Open the MDN Web API index, extract overview topics, open the Fetch API article, and extract the API summary.",
    url: "https://developer.mozilla.org/en-US/docs/Web/API",
    summary: "Read an index page, follow a documentation link, then extract details from the destination."
  }
];
