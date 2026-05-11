import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { projectsApi } from "@/api/projects";
import type { CreateProjectRequest, Project, UUID } from "@/types/api";

export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: () => projectsApi.list(),
  });
}

export function useProject(projectId: UUID | null | undefined) {
  return useQuery<Project>({
    queryKey: ["projects", projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation<Project, unknown, CreateProjectRequest>({
    mutationFn: (req) => projectsApi.create(req),
    onSuccess: (created) => {
      qc.setQueryData<Project[]>(["projects"], (prev) =>
        prev ? [created, ...prev] : [created],
      );
    },
  });
}

export function useProjectFiles(projectId: UUID | null | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "files"],
    queryFn: () => projectsApi.files(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useProjectThreads(projectId: UUID | null | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "threads"],
    queryFn: () => projectsApi.threads(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useThread(
  projectId: UUID | null | undefined,
  threadId: UUID | null | undefined,
) {
  return useQuery({
    queryKey: ["projects", projectId, "threads", threadId],
    queryFn: () => projectsApi.thread(projectId!, threadId!),
    enabled: Boolean(projectId) && Boolean(threadId),
  });
}

export function useProjectSummaries(projectId: UUID | null | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "summaries"],
    queryFn: () => projectsApi.summaries(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useProjectJargonRuns(projectId: UUID | null | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "jargon-runs"],
    queryFn: () => projectsApi.jargonRuns(projectId!),
    enabled: Boolean(projectId),
  });
}
