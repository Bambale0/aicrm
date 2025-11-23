import React, { useCallback, useState, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Panel,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import Button from '../../components/ui/Button';
import { TriggerNode } from './nodes/TriggerNode';
import { StageNode } from './nodes/StageNode';
import { ActionNode } from './nodes/ActionNode';
import { ConditionNode } from './nodes/ConditionNode';
import { AutomationToolbox } from './AutomationToolbox';
import { AutomationProperties } from './AutomationProperties';
import { SimulationMode } from './SimulationMode';
import { ProcessData } from '../../types/automation-board';

const nodeTypes = {
  trigger: TriggerNode,
  stage: StageNode,
  action: ActionNode,
  condition: ConditionNode,
};

const edgeOptions = {
  style: { stroke: '#64748b', strokeWidth: 2 },
};

interface AutomationBoardProps {
  process?: ProcessData;
  automationId?: string;
}

export const AutomationBoard: React.FC<AutomationBoardProps> = ({
  process,
  automationId
}) => {
  // Состояние для адаптивного дизайна
  const [showToolbox, setShowToolbox] = useState(true);
  const [showProperties, setShowProperties] = useState(true);

  // Преобразование данных процесса в ноды и ребра
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!process) {
      return { initialNodes: [], initialEdges: [] };
    }

    const nodes: Node[] = process.stages.map((stage) => ({
      id: stage.id.toString(),
      type: 'stage' as const,
      position: { x: stage.order_index * 250, y: 0 },
      data: {
        label: stage.name,
        stage,
        robots: stage.robots || [],
        config: {},
        color: '#3b82f6'
      },
    }));

    const edges: Edge[] = process.triggers.map((trigger) => ({
      id: trigger.id.toString(),
      source: trigger.source_stage_id.toString(),
      target: trigger.target_stage_id.toString(),
      ...edgeOptions,
      data: { trigger },
      label: trigger.condition || trigger.event_type,
    }));

    return { initialNodes: nodes, initialEdges: edges };
  }, [process]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [simulationMode, setSimulationMode] = useState(false);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());

  const { project, fitView } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        id: `${params.source}-${params.target}-${Date.now()}`,
        source: params.source!,
        target: params.target!,
        sourceHandle: params.sourceHandle || undefined,
        targetHandle: params.targetHandle || undefined,
        ...edgeOptions,
        label: 'переход',
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const position = project({
        x: event.clientX - 250, // sidebar width
        y: event.clientY - 100, // header height
      });

      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type: type as any,
        position,
        data: {
          config: {},
          ...getDefaultNodeData(type)
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [project, setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onSave = useCallback(async () => {
    // Сохранение доски на бэкенд
    const boardData = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data,
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
        label: edge.label,
        data: edge.data,
      })),
    };

    console.log('Saving automation board:', boardData);
    // TODO: API call to save automation
  }, [nodes, edges]);

  // Обновляем nodes со статусом симуляции
  const nodesWithSimulation = useMemo(() => {
    return nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        simulationStatus: activeNodes.has(node.id) ? 'active' : 'inactive'
      }
    }));
  }, [nodes, activeNodes]);

  return (
    <div className="flex h-full bg-gray-900/95">
      {/* Панель инструментов - скрывается на мобильных */}
      <div className={`hidden lg:block ${showToolbox ? 'w-64' : 'w-0'} transition-all duration-300 overflow-hidden`}>
        <AutomationToolbox />
      </div>

      {/* Основная доска */}
      <div className="flex-1 relative min-w-0">
        {/* Мобильные кнопки управления панелями */}
        <div className="lg:hidden absolute top-4 left-4 z-20 flex gap-2">
          <Button
            onClick={() => setShowToolbox(!showToolbox)}
            variant="primary"
            className="text-sm"
          >
            🧰 {showToolbox ? 'Скрыть' : 'Инструменты'}
          </Button>
          <Button
            onClick={() => setShowProperties(!showProperties)}
            variant="secondary"
            className="text-sm"
          >
            ⚙️ {showProperties ? 'Скрыть' : 'Свойства'}
          </Button>
        </div>

        {/* Мобильная панель инструментов (оверлей) */}
        {showToolbox && (
          <div className="lg:hidden absolute top-16 left-4 z-20 card p-4 max-w-xs">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-van-gogh-starry-night-blue">Инструменты</h3>
              <button
                onClick={() => setShowToolbox(false)}
                className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>
            <AutomationToolbox />
          </div>
        )}

        <ReactFlow
          nodes={nodesWithSimulation}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-van-gogh-wheat-field/20"
          minZoom={0.1}
          maxZoom={2}
        >
          <Controls className="bottom-4 left-4" />
          <MiniMap
            nodeColor={(node) => getNodeColor(node.type)}
            position="bottom-right"
            className="hidden sm:block"
          />
          <Background variant={'dots' as any} gap={12} size={1} />

          {/* Панель управления - адаптивная */}
          <Panel position="top-right" className="space-y-2">
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={onSave}
                className="px-3 py-2 bg-van-gogh-chrome-green text-white rounded-lg hover:bg-van-gogh-vermilion transition-colors text-sm"
              >
                💾 Сохранить
              </button>
              <button
                onClick={() => fitView()}
                className="px-3 py-2 bg-van-gogh-ultramarine text-white rounded-lg hover:bg-van-gogh-vermilion transition-colors text-sm"
              >
                👁️ Обзор
              </button>
              <button
                onClick={() => {
                  setNodes([]);
                  setEdges([]);
                }}
                className="px-3 py-2 bg-van-gogh-vermilion text-white rounded-lg hover:bg-van-gogh-ultramarine transition-colors text-sm"
              >
                🗑️ Очистить
              </button>
            </div>
          </Panel>

          {/* Режим симуляции */}
          <SimulationMode
            isActive={simulationMode}
            onToggle={() => setSimulationMode(!simulationMode)}
            onActiveNodesChange={setActiveNodes}
          />
        </ReactFlow>
      </div>

      {/* Панель свойств - скрывается на мобильных */}
      <div className={`hidden lg:block ${showProperties ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden border-l border-gray-700 bg-gray-800/95`}>
        <div className="h-full overflow-y-auto">
          <AutomationProperties
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onUpdate={(data: any) => {
              if (selectedNode) {
                setNodes((nds) =>
                  nds.map((node) =>
                    node.id === selectedNode.id
                      ? { ...node, data: { ...node.data, ...data } }
                      : node
                  )
                );
              }
            }}
          />
        </div>
      </div>

      {/* Мобильная панель свойств (оверлей) */}
      {showProperties && (
        <div className="lg:hidden fixed top-0 right-0 z-30 h-full w-full sm:w-80 card overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h3 className="font-semibold text-van-gogh-starry-night-blue">Свойства</h3>
            <button
              onClick={() => setShowProperties(false)}
              className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors text-xl"
              aria-label="Закрыть"
            >
              ✕
            </button>
          </div>
          <div className="p-4">
            <AutomationProperties
              selectedNode={selectedNode}
              selectedEdge={selectedEdge}
              onUpdate={(data: any) => {
                if (selectedNode) {
                  setNodes((nds) =>
                    nds.map((node) =>
                      node.id === selectedNode.id
                        ? { ...node, data: { ...node.data, ...data } }
                        : node
                    )
                  );
                }
                // Автоматически скрываем панель на мобильных после обновления
                if (window.innerWidth < 1024) {
                  setShowProperties(false);
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const getDefaultNodeData = (type: string) => {
  switch (type) {
    case 'trigger':
      return { label: 'Новый триггер', color: '#ef4444' };
    case 'stage':
      return { label: 'Новая стадия', color: '#3b82f6' };
    case 'action':
      return { label: 'Новое действие', color: '#10b981' };
    case 'condition':
      return { label: 'Условие', color: '#f59e0b' };
    case 'delay':
      return { label: 'Задержка', color: '#8b5cf6' };
    default:
      return { label: 'Узел', color: '#6b7280' };
  }
};

const getNodeColor = (type: string | undefined) => {
  switch (type) {
    case 'trigger': return '#ef4444';
    case 'stage': return '#3b82f6';
    case 'action': return '#10b981';
    case 'condition': return '#f59e0b';
    case 'delay': return '#8b5cf6';
    default: return '#6b7280';
  }
};
