"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchProjectDetail } from "@/lib/projects";
import type { ProjectSummary, TaskItem, InsightItem } from "@/lib/types";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params?.id;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    void fetchProjectDetail(projectId)
      .then((data) => {
        setProject(data.project);
        setTasks(data.tasks ?? []);
        setInsights(data.insights ?? []);
      })
      .catch((err) => setError(err.message));
  }, [projectId]);

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-zinc-500">
              <Link href="/projects" className="text-violet-600 hover:underline">
                Projects
              </Link>{" "}
              / Project {projectId}
            </p>
            <h1 className="text-2xl font-semibold text-zinc-900">{project?.name ?? `Project ${projectId}`}</h1>
            <p className="text-sm text-zinc-500">Phase: {project?.phase ?? "Current"}</p>
          </div>
          <div className="text-right text-xs text-zinc-500">
            <p>Meetings: {project?.meeting_count ?? 0}</p>
            <p>Open tasks: {project?.open_tasks ?? 0}</p>
          </div>
        </div>
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-zinc-900">Open Tasks</h2>
            {tasks.length === 0 ? (
              <p className="mt-2 text-xs text-zinc-500">No AI-tracked tasks yet.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm text-zinc-700">
                {tasks.map((task) => (
                  <li key={task.id} className="rounded-md border border-gray-100 p-2">
                    <p className="font-medium text-zinc-900">{task.title}</p>
                    {task.description && (
                      <p className="text-xs text-zinc-500">{task.description}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-zinc-900">Recent Insights</h2>
            {insights.length === 0 ? (
              <p className="mt-2 text-xs text-zinc-500">No insights logged yet.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm text-zinc-700">
                {insights.map((insight) => (
                  <li key={insight.id ?? insight.summary} className="rounded-md border border-gray-100 p-2">
                    <p className="text-xs uppercase text-zinc-500">{insight.severity ?? "info"}</p>
                    <p>{insight.summary}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
