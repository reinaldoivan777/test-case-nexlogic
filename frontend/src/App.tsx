import { useCallback, useEffect, useMemo, useState } from "react";
import { Background, Controls, MiniMap, ReactFlow, ReactFlowProvider, useEdgesState, useNodesState } from "@xyflow/react";
import type { Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { api } from "./api";
import { BaseNode } from "./nodes/BaseNode";
import { RetrievalNode } from "./nodes/RetrievalNode";
import type { KnowledgeBase, Workflow, WorkflowNode, WorkflowNodeData, WorkflowRun } from "./types";

type AppState = {
  workflow: Workflow | null;
  knowledgeBases: KnowledgeBase[];
};

function Builder() {
  const [appState, setAppState] = useState<AppState>({ workflow: null, knowledgeBases: [] });
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [query, setQuery] = useState("");
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [latestRun, setLatestRun] = useState<WorkflowRun | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);

  const updateRetrievalNode = useCallback((changes: Partial<WorkflowNodeData>) => {
    setNodes((currentNodes) => currentNodes.map((node) => (
      node.id === "retrieval" ? { ...node, data: { ...node.data, ...changes } } : node
    )));
  }, [setNodes]);

  const loadRuns = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const response = await api.getRuns();
      setRuns(response.data);
      setLatestRun((currentRun) => currentRun || response.data[0] || null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load preview history");
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    async function loadBaseline() {
      try {
        const [workflowResponse, knowledgeBaseResponse] = await Promise.all([
          api.getDefaultWorkflow(),
          api.getKnowledgeBases(),
        ]);
        const workflow = workflowResponse.data;
        const knowledgeBases = knowledgeBaseResponse.data;
        setAppState({ workflow, knowledgeBases });
        setNodes((workflow.nodes || []).map((node) => ({
          ...node,
          data: node.id === "retrieval"
            ? { ...node.data, knowledgeBases, onChange: updateRetrievalNode }
            : node.data,
        })));
        setEdges(workflow.edges || []);
        await loadRuns();
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load the baseline workflow");
      }
    }
    void loadBaseline();
  }, [loadRuns, setEdges, setNodes, updateRetrievalNode]);

  const nodeTypes = useMemo(() => ({ start: BaseNode, retrieval: RetrievalNode, llm: BaseNode, answer: BaseNode }), []);

  const previewWorkflow = async () => {
    setError("");
    setIsPreviewing(true);
    try {
      const run = await api.previewWorkflow(query, appState.workflow?.id, nodes, edges);
      setLatestRun(run);
      await loadRuns();
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "Unable to preview workflow");
    } finally {
      setIsPreviewing(false);
    }
  };

  const formatTimestamp = (value: string) => new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">NEXLOGIC ENGINEERING TEST</p>
          <h1>Mini RAG Workflow Builder</h1>
        </div>
        <span className="status">Baseline ready</span>
      </header>

      {error && <div className="notice" role="alert">{error}</div>}

      <section className="workspace">
        <div className="canvas-panel">
          <div className="panel-heading">
            <div>
              <h2>{appState.workflow?.name || "Loading workflow…"}</h2>
              <p>Configure the retrieval node, then preview the RAG execution.</p>
            </div>
          </div>
          <div className="flow-canvas">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable
            >
              <Background gap={20} color="#1f3540" />
              <Controls showInteractive={false} />
              <MiniMap
                nodeColor="#4bddc4"
                maskColor="rgba(6, 18, 21, 0.68)"
                pannable
                zoomable
              />
            </ReactFlow>
          </div>
        </div>

        <aside className="preview-panel">
          <div className="panel-heading">
            <div>
              <h2>Preview</h2>
              <p>Ask a question about the seeded Nexlogic knowledge base.</p>
            </div>
          </div>
          <label className="query-label" htmlFor="query">Query</label>
          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="How does a Nexlogic RAG workflow work?"
            rows={5}
          />
          <button type="button" onClick={() => void previewWorkflow()} disabled={isPreviewing || !query.trim()}>
            {isPreviewing ? "Running preview…" : "Preview workflow"}
          </button>

          <section className="result-section">
            <h3>Answer</h3>
            {isPreviewing ? (
              <p className="placeholder">Generating answer…</p>
            ) : latestRun ? (
              <p>{latestRun.answer}</p>
            ) : (
              <p className="placeholder">Run the workflow to inspect its answer and citations.</p>
            )}
          </section>

          <section className="result-section">
            <h3>Citations</h3>
            {latestRun?.citations.length ? (
              <ul className="result-list">
                {latestRun.citations.map((citation) => (
                  <li key={citation.chunk_id}>
                    <span>{citation.document_name}</span>
                    <strong>{citation.score.toFixed(2)}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="placeholder">Citations will appear after a successful preview.</p>
            )}
          </section>

          <section className="result-section">
            <h3>Execution trace</h3>
            {latestRun?.trace.length ? (
              <ol className="trace-list">
                {latestRun.trace.map((item) => (
                  <li key={item.node_id}>
                    <span>{item.node_id}</span>
                    <strong>{item.retrieved_count ? `${item.status} · ${item.retrieved_count} chunks` : item.status}</strong>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="placeholder">Trace events will appear after a successful preview.</p>
            )}
          </section>

          <section className="result-section">
            <h3>Recent runs</h3>
            {isHistoryLoading ? (
              <p className="placeholder">Loading history…</p>
            ) : runs.length ? (
              <ul className="history-list">
                {runs.map((run) => (
                  <li key={run.id}>
                    <button type="button" className="history-button" onClick={() => setLatestRun(run)}>
                      <span>{run.query}</span>
                      <small>{formatTimestamp(run.created_at)}</small>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="placeholder">Preview history will appear here.</p>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

export default function App() {
  return <ReactFlowProvider><Builder /></ReactFlowProvider>;
}
