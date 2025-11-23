export interface AutomationNode {
  id: string;
  type: 'trigger' | 'stage' | 'action' | 'condition' | 'delay';
  position: { x: number; y: number };
  data: NodeData;
  width?: number;
  height?: number;
}

export interface NodeData {
  label: string;
  description?: string;
  config: Record<string, any>;
  color?: string;
  icon?: string;
}

export interface AutomationEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  condition?: string;
  data?: {
    trigger?: any;
  };
}

export interface AutomationBoard {
  id: string;
  name: string;
  description: string;
  nodes: AutomationNode[];
  edges: AutomationEdge[];
  zoom: number;
  position: [number, number];
  createdAt: Date;
  updatedAt: Date;
}

export interface ProcessData {
  id: number;
  name: string;
  stages: Array<{
    id: number;
    name: string;
    order_index: number;
    robots?: any[];
  }>;
  triggers: Array<{
    id: number;
    event_type: string;
    source_stage_id: number;
    target_stage_id: number;
    condition?: string;
  }>;
}
