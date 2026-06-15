import { getTasks } from "./api";
import type { Run } from "./types";

type TaskListener = (tasks: Run[]) => void;

let cachedTasks: Run[] | null = null;
let pendingRefresh: Promise<Run[]> | null = null;
const listeners = new Set<TaskListener>();

function publishTasks(tasks: Run[]) {
  for (const listener of listeners) {
    listener(tasks);
  }
}

export function getCachedTasks() {
  return cachedTasks;
}

export function subscribeTaskCache(listener: TaskListener) {
  listeners.add(listener);
  if (cachedTasks) {
    listener(cachedTasks);
  }
  return () => {
    listeners.delete(listener);
  };
}

export async function refreshTaskCache() {
  if (pendingRefresh) return pendingRefresh;
  pendingRefresh = getTasks()
    .then((tasks) => {
      cachedTasks = tasks;
      publishTasks(tasks);
      return tasks;
    })
    .finally(() => {
      pendingRefresh = null;
    });
  return pendingRefresh;
}
