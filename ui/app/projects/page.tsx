"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchProjects } from "@/lib/projects";
import type { ProjectSummary } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchProjects()
      .then((data) => setProjects(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Projects</h1>
          <p className="text-sm text-zinc-500">AI-tracked meetings, tasks, and risks.</p>
        </div>
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="grid gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          {projects.length === 0 && !error ? (
            <p className="text-sm text-zinc-500">No projects found. Ingest transcripts to get started.</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {projects.map((project) => (
                <Link
                  key={project.project_id}
                  href={`/projects/${project.project_id}`}
                  className="rounded-lg border border-gray-200 p-4 transition hover:border-violet-300 hover:shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{project.name ?? `Project ${project.project_id}`}</p>
                      <p className="text-xs text-zinc-500">Phase: {project.phase ?? "Current"}</p>
                    </div>
                    <span className="text-xs font-semibold text-violet-600">
                      {project.open_tasks} open tasks
                    </span>
                  </div>
                  <div className="mt-3 flex gap-6 text-xs text-zinc-500">
                    <span>{project.meeting_count} meetings</span>
                    <span>Last meeting: {project.last_meeting_at ?? "N/A"}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
