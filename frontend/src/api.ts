import type { Edge } from "@xyflow/react";
import type { KnowledgeBase, Workflow, WorkflowNode, WorkflowRun } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5050/api";

type ApiError = { error?: { message?: string } };

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as ApiError;
    throw new Error(error.error?.message || "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  getKnowledgeBases: () => request<{ data: KnowledgeBase[] }>("/knowledge-bases"),
  getDefaultWorkflow: () => request<{ data: Workflow }>("/workflows/default"),
  getRuns: () => request<{ data: WorkflowRun[] }>("/runs?workflow_id=default"),
  previewWorkflow: (query: string, workflowId: string | undefined, nodes: WorkflowNode[], edges: Edge[]) =>
    request<WorkflowRun>("/workflows/preview", {
      method: "POST",
      body: JSON.stringify({ query, workflow_id: workflowId, nodes, edges }),
    }),
};
