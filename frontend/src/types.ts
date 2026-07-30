import type { Edge, Node } from "@xyflow/react";

export type KnowledgeBase = {
  id: string;
  name: string;
  description: string;
};

export type WorkflowNodeData = {
  label: string;
  description?: string;
  knowledge_base_id?: string;
  top_k?: number;
  prompt_template?: string;
  knowledgeBases?: KnowledgeBase[];
  onChange?: (changes: Partial<WorkflowNodeData>) => void;
};

export type WorkflowNode = Node<WorkflowNodeData>;

export type Workflow = {
  id?: string;
  name?: string;
  nodes?: WorkflowNode[];
  edges?: Edge[];
};

export type Citation = {
  chunk_id: string;
  document_name: string;
  score: number;
};

export type TraceItem = {
  node_id: string;
  status: "succeeded" | "failed";
  retrieved_count?: number;
};

export type WorkflowRun = {
  id: string;
  workflow_id: string;
  query: string;
  answer: string;
  citations: Citation[];
  trace: TraceItem[];
  created_at: string;
};
