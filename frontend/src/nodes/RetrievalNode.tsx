import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import type { KnowledgeBase, WorkflowNodeData } from "../types";

type RetrievalNodeData = WorkflowNodeData & {
  knowledgeBases?: KnowledgeBase[];
  onChange?: (changes: Partial<WorkflowNodeData>) => void;
};

type Props = NodeProps & { data: RetrievalNodeData };

export function RetrievalNode({ data, selected }: Props) {
  const update = (changes: Partial<WorkflowNodeData>) => {
    data.onChange?.(changes);
  };

  return (
    <div className={`flow-node retrieval-node ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <span className="node-label">{data.label}</span>
      <label>
        Knowledge base
        <select value={data.knowledge_base_id || ""} onChange={(event) => update({ knowledge_base_id: event.target.value })}>
          <option value="">Select knowledge base</option>
          {data.knowledgeBases?.map((knowledgeBase) => (
            <option key={knowledgeBase.id} value={knowledgeBase.id}>{knowledgeBase.name}</option>
          ))}
        </select>
      </label>
      <label>
        Top K
        <input type="number" min="1" max="5" value={data.top_k || 3} onChange={(event) => update({ top_k: Number(event.target.value) })} />
      </label>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
