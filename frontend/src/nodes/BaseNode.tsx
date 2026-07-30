import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import type { WorkflowNodeData } from "../types";

type Props = NodeProps & { data: WorkflowNodeData };

export function BaseNode({ data, selected }: Props) {
  return (
    <div className={`flow-node ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <span className="node-label">{data.label}</span>
      {data.description && <span className="node-description">{data.description}</span>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
