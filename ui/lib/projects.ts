import type { ProjectSummary, TaskItem, InsightItem } from "@/lib/types";

export async function fetchProjects(): Promise<ProjectSummary[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) throw new Error("Failed to load projects");
  const payload = await res.json();
  return payload.projects ?? [];
}

export interface ProjectDetailResponse {
  project: ProjectSummary & Record<string, any>;
  tasks: TaskItem[];
  insights: InsightItem[];
}

export async function fetchProjectDetail(id: string | number): Promise<ProjectDetailResponse> {
  const res = await fetch(`/api/projects/${id}`);
  if (!res.ok) throw new Error("Failed to load project detail");
  return res.json();
}

export async function postFirefliesIngestion(data: { path: string; project_id?: number; dry_run?: boolean }) {
  const res = await fetch("/api/ingest/fireflies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Ingestion failed");
  return res.json();
}
