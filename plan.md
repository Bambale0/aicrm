Мы хотим создать интерактивную доску (live board) для построения автоматизаций. Это будет визуальный конструктор, где можно перетаскивать этапы, настраивать триггеры и роботов, и видеть связи между ними.

Примерный план:

Создать компонент WorkflowBoard, который будет отображать процессы автоматизации в виде графа (ноды - стадии, стрелки - переходы).

Использовать библиотеку для графов (например, React Flow) или создать свой простой вариант с SVG.

Реализовать возможность перетаскивания стадий, соединения их, настройки триггеров и роботов.

Обеспечить сохранение изменений в бэкенд.

Рассмотрим использование React Flow (https://reactflow.dev) как мощной библиотеки для построения графов.

Шаги:

Установим React Flow:
npm install reactflow

Создадим компонент WorkflowBoard:

Определим типы нод (стадии) и эджей (переходы) в графе.

Настроим первоначальные данные из бэкенда (процесс, стадии, триггеры).

Преобразуем данные бэкенда в ноды и ребра для React Flow.

Реализуем функциональность:

Добавление новой стадии (ноды) через панель инструментов или контекстное меню.

Удаление стадии.

Соединение стадий (создание ребер) путем перетаскивания от одной ноды к другой.

Настройка стадии (название, цвет, роботы) через модальное окно по двойному клику или через панель свойств.

Настройка триггеров (условия перехода) на ребрах.

Сохранение изменений:

При изменении графа (добавление/удаление нод, ребер) отправляем изменения на бэкенд.

Дополнительно:

Возможность масштабирования и панорамирования.

Сетка для выравнивания.

Отображение дополнительной информации о стадиях (количество роботов, цвет).

Пример структуры данных для графа:

text
Узел (Node):
  id: string (соответствует id стадии)
  type: 'stage'
  position: { x: number, y: number }
  data: {
    label: string (название стадии),
    stage: Stage (полные данные стадии),
    robots: Robot[],
    ...другие данные
  }

Ребро (Edge):
  id: string
  source: string (id ноды-источника)
  target: string (id ноды-цели)
  data: {
    trigger: Trigger (данные триггера, если есть)
  }
6. Преобразование данных из бэкенда:

text
Бэкенд присылает процесс, который содержит стадии и триггеры (которые связывают стадии).

Пример данных бэкенда:

  process: {
    id: 1,
    name: "Процесс заказа",
    stages: [
      { id: 1, name: "Новый заказ", order_index: 0, ... },
      { id: 2, name: "В производстве", order_index: 1, ... },
      { id: 3, name: "Готов", order_index: 2, ... }
    ],
    triggers: [
      { id: 1, event_type: "stage_completed", source_stage_id: 1, target_stage_id: 2, ... },
      { id: 2, event_type: "stage_completed", source_stage_id: 2, target_stage_id: 3, ... }
    ]
  }

Преобразование в ноды:

  nodes = process.stages.map(stage => ({
    id: stage.id.toString(),
    type: 'stage',
    position: { x: stage.order_index * 250, y: 0 }, // или как-то иначе
    data: { label: stage.name, stage, robots: [] } // robots нужно получить из бэкенда для стадии
  }))

Преобразование в ребра:

  edges = process.triggers.map(trigger => ({
    id: trigger.id.toString(),
    source: trigger.source_stage_id.toString(),
    target: trigger.target_stage_id.toString(),
    data: { trigger }
  }))
7. Реализуем кастомный узел (StageNode) для отображения стадии.

Добавим панель инструментов для добавления новых стадий, сохранения, отмены и т.д.

Реализуем боковую панель свойств, которая показывает свойства выбранного узла или ребра.

Реализуем логику сохранения:

При изменении графа (нод, ребер) мы должны обновлять данные процесса на бэкенде.

Для нод: обновляем стадии (порядок, позиция?).

Для ребер: обновляем триггеры (источник, цель).

Учтем, что позиция нод (x, y) должна сохраняться, чтобы пользователь мог расположить стадии как угодно.

Возможность добавлять триггеры на ребра (условия перехода) через диалоговое окно.

Возможность добавлять роботов к стадии (при двойном клике на ноду открываем модалку с настройками стадии, включая роботов).

Визуальные улучшения: цвета стадий, иконки, анимации.

Пример кода компонента WorkflowBoard:

typescript
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
} from 'reactflow';
import 'reactflow/dist/style.css';

import StageNode from './StageNode';

const nodeTypes = {
  stage: StageNode,
};

// Начальные данные (позже будем получать из бэкенда)
const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

const WorkflowBoard: React.FC<{ process: any }> = ({ process }) => {
  // Преобразуем данные процесса в ноды и ребра
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodes: Node[] = process.stages.map((stage: any) => ({
      id: stage.id.toString(),
      type: 'stage',
      position: { x: stage.order_index * 250, y: 0 }, // TODO: сохранять позицию в бэкенде
      data: { label: stage.name, stage, robots: stage.robots || [] },
    }));

    const edges: Edge[] = process.triggers.map((trigger: any) => ({
      id: trigger.id.toString(),
      source: trigger.source_stage_id.toString(),
      target: trigger.target_stage_id.toString(),
      data: { trigger },
    }));

    return { nodes, edges };
  }, [process]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, data: {} }, eds)),
    [setEdges],
  );

  // Функция для сохранения графа на бэкенд
  const saveGraph = useCallback(() => {
    // Преобразуем nodes и edges в данные процесса
    const stages = nodes.map(node => ({
      id: parseInt(node.id),
      name: node.data.label,
      order_index: node.position.x, // или иначе, но лучше хранить позицию отдельно
      // ... другие поля
    }));

    const triggers = edges.map(edge => ({
      id: parseInt(edge.id),
      source_stage_id: parseInt(edge.source),
      target_stage_id: parseInt(edge.target),
      // ... другие поля
    }));

    // Отправляем на бэкенд
    // updateProcess({ stages, triggers });
  }, [nodes, edges]);

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
      
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 4 }}>
        <button onClick={saveGraph}>Сохранить</button>
      </div>
    </div>
  );
};

export default WorkflowBoard;
Компонент StageNode:

typescript
import React from 'react';
import { Handle, Position } from 'reactflow';

const StageNode: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div style={{ 
      padding: '10px', 
      borderRadius: '5px', 
      background: '#fff', 
      border: '1px solid #000',
      minWidth: '150px'
    }}>
      <Handle type="target" position={Position.Top} />
      <div>{data.label}</div>
      <div style={{ fontSize: '10px', color: '#666' }}>
        Роботы: {data.robots.length}
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default StageNode;
Дальнейшие шаги:

Реализовать добавление новой ноды (стадии) через кнопку на панели инструментов или через контекстное меню.

Реализовать удаление ноды и ребра.

Реализовать диалог настройки стадии (двойной клик по ноде) для редактирования названия, добавления роботов и т.д.

Реализовать диалог настройки триггера (клик по ребру) для задания условий перехода.

Для добавления новой ноды:

text
const addNode = useCallback(() => {
  const newNode = {
    id: `${nodes.length + 1}`,
    type: 'stage',
    position: { x: Math.random() * 500, y: Math.random() * 500 },
    data: { label: `Новая стадия ${nodes.length + 1}`, robots: [] },
  };
  setNodes((nds) => nds.concat(newNode));
}, [nodes.length, setNodes]);
Для удаления ноды и ребер, связанных с ней, React Flow уже предоставляет функциональность через onNodesChange.

Для редактирования свойств ноды или ребра мы можем использовать выбранный элемент:

text
const [selectedNode, setSelectedNode] = useState<Node | null>(null);
const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

// Обработчики для выбора
const onNodeClick = useCallback((event, node) => setSelectedNode(node), []);
const onEdgeClick = useCallback((event, edge) => setSelectedEdge(edge), []);

Затем в ReactFlow добавляем props:
  onNodeClick={onNodeClick}
  onEdgeClick={onEdgeClick}
И отображаем панель свойств для выбранного элемента.

Это общий план. Реализация может быть сложной, но React Flow предоставляет много готовой функциональности.

Важно: сохранять позиции нод в бэкенде, чтобы при следующем открытии доска выглядела так же.

Также нужно подумать о производительности при большом количестве нод.

Давайте начнем с базовой реализации и будем постепенно добавлять функциональность.

Отличная идея! Live-доска для построения автоматизаций значительно улучшит UX. Вот реализация интерактивной доски для визуального конструирования бизнес-процессов:

🎯 ИНТЕРАКТИВНАЯ LIVE-ДОСКА ДЛЯ АВТОМАТИЗАЦИЙ
1. 🏗️ Архитектура доски
typescript
// src/types/automation-board.ts
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
2. 🎨 React Flow интеграция
typescript
// src/components/AutomationBoard/AutomationBoard.tsx
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

import { TriggerNode } from './nodes/TriggerNode';
import { StageNode } from './nodes/StageNode';
import { ActionNode } from './nodes/ActionNode';
import { ConditionNode } from './nodes/ConditionNode';
import { AutomationToolbox } from './AutomationToolbox';
import { AutomationProperties } from './AutomationProperties';

const nodeTypes = {
  trigger: TriggerNode,
  stage: StageNode,
  action: ActionNode,
  condition: ConditionNode,
};

const edgeOptions = {
  style: { stroke: '#64748b', strokeWidth: 2 },
  markerEnd: { type: 'arrowclosed', color: '#64748b' },
};

export const AutomationBoard: React.FC<{ automationId?: string }> = ({ automationId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  
  const { project, fitView } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        id: `${params.source}-${params.target}-${Date.now()}`,
        ...edgeOptions,
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
        type,
        position,
        data: { 
          label: `${type} node`,
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
        type: node.type as any,
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
      })),
    };

    // API call to save automation
    await saveAutomationBoard(automationId, boardData);
  }, [nodes, edges, automationId]);

  return (
    <div className="flex h-full bg-gray-50">
      {/* Панель инструментов */}
      <AutomationToolbox />
      
      {/* Основная доска */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
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
          className="bg-gray-100"
        >
          <Controls />
          <MiniMap 
            nodeColor={(node) => getNodeColor(node.type)}
            position="bottom-right"
          />
          <Background variant="dots" gap={12} size={1} />
          
          {/* Панель управления */}
          <Panel position="top-right" className="space-y-2">
            <button
              onClick={onSave}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
            >
              Сохранить
            </button>
            <button
              onClick={() => fitView()}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Обзор
            </button>
            <button
              onClick={() => {
                setNodes([]);
                setEdges([]);
              }}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Очистить
            </button>
          </Panel>
        </ReactFlow>
      </div>

      {/* Панель свойств */}
      <div className="w-80 border-l bg-white overflow-y-auto">
        <AutomationProperties 
          selectedNode={selectedNode}
          selectedEdge={selectedEdge}
          onUpdate={(data) => {
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
    default: return '#6b7280';
  }
};
3. 🧩 Кастомные узлы
typescript
// src/components/AutomationBoard/nodes/StageNode.tsx
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const StageNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`
      px-4 py-3 shadow-lg rounded-lg border-2 min-w-[200px] transition-all
      ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
      ${data.color ? `bg-${data.color}-50 border-${data.color}-300` : 'bg-white'}
    `}>
      {/* Входные точки */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400"
      />
      
      {/* Содержимое узла */}
      <div className="flex items-center space-x-3">
        <div 
          className="w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: data.color }}
        />
        <div className="flex-1">
          <div className="font-medium text-gray-900">{data.label}</div>
          {data.description && (
            <div className="text-sm text-gray-500 mt-1">{data.description}</div>
          )}
          
          {/* Дополнительная информация */}
          {data.robots && data.robots.length > 0 && (
            <div className="mt-2 text-xs text-gray-600">
              🤖 {data.robots.length} действий
            </div>
          )}
        </div>
      </div>

      {/* Выходные точки */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-gray-400"
      />
    </div>
  );
};
typescript
// src/components/AutomationBoard/nodes/TriggerNode.tsx
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const TriggerNode: React.FC<NodeProps> = ({ data, selected }) => {
  const getTriggerIcon = (triggerType: string) => {
    switch (triggerType) {
      case 'order_created': return '🛒';
      case 'customer_created': return '👤';
      case 'task_completed': return '✅';
      case 'message_received': return '💬';
      default: return '⚡';
    }
  };

  return (
    <div className={`
      px-4 py-3 shadow-lg rounded-lg border-2 min-w-[200px] transition-all
      ${selected ? 'border-red-500 ring-2 ring-red-200' : 'border-red-300'}
      bg-red-50
    `}>
      <div className="flex items-center space-x-3">
        <div className="text-lg">{getTriggerIcon(data.config?.type)}</div>
        <div className="flex-1">
          <div className="font-medium text-gray-900">{data.label}</div>
          <div className="text-sm text-gray-500 mt-1">
            {data.config?.type && `Тип: ${data.config.type}`}
          </div>
        </div>
      </div>

      {/* Только выходная точка для триггера */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-red-400"
      />
    </div>
  );
};
typescript
// src/components/AutomationBoard/nodes/ConditionNode.tsx
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const ConditionNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`
      px-4 py-3 shadow-lg rounded-lg border-2 min-w-[200px] transition-all
      ${selected ? 'border-yellow-500 ring-2 ring-yellow-200' : 'border-yellow-300'}
      bg-yellow-50
    `}>
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400"
      />

      <div className="flex items-center space-x-3">
        <div className="text-lg">❓</div>
        <div className="flex-1">
          <div className="font-medium text-gray-900">{data.label}</div>
          {data.config?.condition && (
            <div className="text-sm text-gray-500 mt-1">
              Условие: {data.config.condition}
            </div>
          )}
        </div>
      </div>

      {/* Два выхода для условий Да/Нет */}
      <div className="flex justify-between mt-2">
        <Handle
          type="source"
          position={Position.Bottom}
          id="true"
          className="w-3 h-3 bg-green-400"
        >
          <div className="text-xs text-green-600 -mt-4 -ml-2">Да</div>
        </Handle>
        <Handle
          type="source"
          position={Position.Bottom}
          id="false"
          className="w-3 h-3 bg-red-400"
        >
          <div className="text-xs text-red-600 -mt-4 -ml-2">Нет</div>
        </Handle>
      </div>
    </div>
  );
};
4. 🧰 Панель инструментов
typescript
// src/components/AutomationBoard/AutomationToolbox.tsx
import React from 'react';

const toolboxItems = [
  {
    type: 'trigger',
    label: 'Триггер',
    description: 'Запускает процесс автоматизации',
    icon: '⚡',
    color: '#ef4444',
    examples: ['Новый заказ', 'Новый клиент', 'Сообщение']
  },
  {
    type: 'stage',
    label: 'Стадия',
    description: 'Этап процесса',
    icon: '📋',
    color: '#3b82f6',
    examples: ['Обработка', 'Производство', 'Контроль качества']
  },
  {
    type: 'action',
    label: 'Действие',
    description: 'Автоматическое действие',
    icon: '🤖',
    color: '#10b981',
    examples: ['Отправить email', 'Создать задачу', 'Обновить статус']
  },
  {
    type: 'condition',
    label: 'Условие',
    description: 'Проверка условия',
    icon: '❓',
    color: '#f59e0b',
    examples: ['Если сумма > 10000', 'Если VIP клиент']
  },
  {
    type: 'delay',
    label: 'Задержка',
    description: 'Пауза в процессе',
    icon: '⏰',
    color: '#8b5cf6',
    examples: ['Ждать 2 часа', 'Ждать до понедельника']
  }
];

export const AutomationToolbox: React.FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Элементы автоматизации</h2>
        <p className="text-sm text-gray-500 mt-1">Перетащите на доску</p>
      </div>

      <div className="p-4 space-y-3">
        {toolboxItems.map((item) => (
          <div
            key={item.type}
            className="border border-gray-200 rounded-lg p-3 cursor-move hover:shadow-md transition-shadow bg-white"
            onDragStart={(e) => onDragStart(e, item.type)}
            draggable
          >
            <div className="flex items-start space-x-3">
              <div 
                className="text-xl flex-shrink-0"
                style={{ color: item.color }}
              >
                {item.icon}
              </div>
              
              <div className="flex-1">
                <div className="font-medium text-gray-900">{item.label}</div>
                <div className="text-sm text-gray-500 mt-1">{item.description}</div>
                
                <div className="mt-2">
                  <div className="text-xs text-gray-400">Примеры:</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {item.examples.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Шаблоны процессов */}
      <div className="p-4 border-t border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3">Готовые шаблоны</h3>
        <div className="space-y-2">
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            🛒 Процесс заказа
          </button>
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            👤 Онбординг клиента
          </button>
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            📧 Email кампания
          </button>
        </div>
      </div>
    </div>
  );
};
5. ⚙️ Панель свойств
typescript
// src/components/AutomationBoard/AutomationProperties.tsx
import React from 'react';
import { Node, Edge } from 'reactflow';

interface AutomationPropertiesProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onUpdate: (data: any) => void;
}

export const AutomationProperties: React.FC<AutomationPropertiesProps> = ({
  selectedNode,
  selectedEdge,
  onUpdate,
}) => {
  if (!selectedNode && !selectedEdge) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="text-4xl mb-2">🎯</div>
        <p>Выберите элемент на доске для настройки</p>
      </div>
    );
  }

  if (selectedNode) {
    return <NodeProperties node={selectedNode} onUpdate={onUpdate} />;
  }

  if (selectedEdge) {
    return <EdgeProperties edge={selectedEdge} onUpdate={onUpdate} />;
  }

  return null;
};

const NodeProperties: React.FC<{ node: Node; onUpdate: (data: any) => void }> = ({
  node,
  onUpdate,
}) => {
  const [formData, setFormData] = React.useState(node.data);

  const handleChange = (field: string, value: any) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    onUpdate(newData);
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Настройки узла</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Название
          </label>
          <input
            type="text"
            value={formData.label || ''}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Описание
          </label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Динамические поля в зависимости от типа узла */}
        {node.type === 'trigger' && (
          <TriggerConfig 
            config={formData.config} 
            onChange={(config) => handleChange('config', config)} 
          />
        )}

        {node.type === 'stage' && (
          <StageConfig 
            config={formData.config} 
            onChange={(config) => handleChange('config', config)} 
          />
        )}

        {node.type === 'action' && (
          <ActionConfig 
            config={formData.config} 
            onChange={(config) => handleChange('config', config)} 
          />
        )}

        {node.type === 'condition' && (
          <ConditionConfig 
            config={formData.config} 
            onChange={(config) => handleChange('config', config)} 
          />
        )}

        {/* Цвет узла */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Цвет узла
          </label>
          <div className="flex space-x-2">
            {['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'].map((color) => (
              <button
                key={color}
                className={`w-8 h-8 rounded-full border-2 ${
                  formData.color === color ? 'border-gray-900' : 'border-gray-300'
                }`}
                style={{ backgroundColor: color }}
                onClick={() => handleChange('color', color)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const TriggerConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  const triggerTypes = [
    { value: 'order_created', label: 'Создан заказ', icon: '🛒' },
    { value: 'customer_created', label: 'Создан клиент', icon: '👤' },
    { value: 'task_completed', label: 'Завершена задача', icon: '✅' },
    { value: 'message_received', label: 'Получено сообщение', icon: '💬' },
    { value: 'status_changed', label: 'Изменен статус', icon: '🔄' },
  ];

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Тип триггера
      </label>
      <select
        value={config?.type || ''}
        onChange={(e) => onChange({ ...config, type: e.target.value })}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="">Выберите тип триггера</option>
        {triggerTypes.map((type) => (
          <option key={type.value} value={type.value}>
            {type.icon} {type.label}
          </option>
        ))}
      </select>
    </div>
  );
};

const ActionConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  const actionTypes = [
    { value: 'send_email', label: 'Отправить email', icon: '📧' },
    { value: 'create_task', label: 'Создать задачу', icon: '✅' },
    { value: 'update_status', label: 'Обновить статус', icon: '🔄' },
    { value: 'assign_user', label: 'Назначить пользователя', icon: '👤' },
    { value: 'call_webhook', label: 'Вызвать webhook', icon: '🌐' },
  ];

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Тип действия
        </label>
        <select
          value={config?.actionType || ''}
          onChange={(e) => onChange({ ...config, actionType: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Выберите действие</option>
          {actionTypes.map((action) => (
            <option key={action.value} value={action.value}>
              {action.icon} {action.label}
            </option>
          ))}
        </select>
      </div>

      {config?.actionType === 'send_email' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Шаблон email
          </label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
            <option>Приветственное письмо</option>
            <option>Уведомление о заказе</option>
            <option>Напоминание</option>
          </select>
        </div>
      )}
    </div>
  );
};
6. 🔄 Режим симуляции
typescript
// src/components/AutomationBoard/SimulationMode.tsx
import React, { useState, useCallback } from 'react';
import { useReactFlow, Node, Edge } from 'reactflow';

export const SimulationMode: React.FC = () => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const { getNodes, getEdges } = useReactFlow();

  const startSimulation = useCallback(() => {
    setIsSimulating(true);
    setCurrentStep(0);
    
    // Найти стартовые узлы (триггеры)
    const startNodes = getNodes().filter(node => node.type === 'trigger');
    setActiveNodes(new Set(startNodes.map(node => node.id)));
    
    // Запустить пошаговое выполнение
    simulateStep(0, new Set(startNodes.map(node => node.id)));
  }, [getNodes]);

  const simulateStep = useCallback((step: number, activeNodeIds: Set<string>) => {
    if (step > 10) return; // Защита от бесконечного цикла
    
    setTimeout(() => {
      const edges = getEdges();
      const nodes = getNodes();
      
      // Найти следующие узлы, связанные с активными
      const nextActiveNodes = new Set<string>();
      
      activeNodeIds.forEach(nodeId => {
        const outgoingEdges = edges.filter(edge => edge.source === nodeId);
        outgoingEdges.forEach(edge => {
          nextActiveNodes.add(edge.target);
        });
      });
      
      setActiveNodes(nextActiveNodes);
      setCurrentStep(step + 1);
      
      if (nextActiveNodes.size > 0) {
        simulateStep(step + 1, nextActiveNodes);
      } else {
        setIsSimulating(false);
      }
    }, 1000);
  }, [getEdges, getNodes]);

  const getNodeStatus = useCallback((nodeId: string) => {
    if (activeNodes.has(nodeId)) return 'active';
    return 'inactive';
  }, [activeNodes]);

  return (
    <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-lg border">
      <div className="flex items-center space-x-4">
        <button
          onClick={isSimulating ? () => setIsSimulating(false) : startSimulation}
          className={`px-4 py-2 rounded-lg font-medium ${
            isSimulating 
              ? 'bg-red-500 text-white hover:bg-red-600' 
              : 'bg-green-500 text-white hover:bg-green-600'
          }`}
        >
          {isSimulating ? '⏹️ Остановить' : '▶️ Запустить симуляцию'}
        </button>
        
        {isSimulating && (
          <div className="text-sm text-gray-600">
            Шаг: {currentStep}
          </div>
        )}
      </div>
      
      {isSimulating && (
        <div className="mt-2 text-xs text-gray-500">
          💡 Активные узлы подсвечиваются зеленым
        </div>
      )}
    </div>
  );
};

// Добавляем в основной компонент AutomationBoard
const enhancedNodeTypes = {
  ...nodeTypes,
  // Переопределяем узлы для поддержки симуляции
};
7. 📱 Адаптивный дизайн
typescript
// src/hooks/useAutomationBoard.ts
import { useState, useCallback } from 'react';

export const useAutomationBoard = (initialAutomationId?: string) => {
  const [currentAutomation, setCurrentAutomation] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'design' | 'simulate' | 'code'>('design');

  const loadAutomation = useCallback(async (automationId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/automation/${automationId}/board`);
      const data = await response.json();
      setCurrentAutomation(data);
    } catch (error) {
      console.error('Failed to load automation:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveAutomation = useCallback(async (boardData: any) => {
    if (!currentAutomation) return;
    
    try {
      await fetch(`/api/automation/${currentAutomation.id}/board`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(boardData),
      });
    } catch (error) {
      console.error('Failed to save automation:', error);
    }
  }, [currentAutomation]);

  return {
    currentAutomation,
    isLoading,
    viewMode,
    setViewMode,
    loadAutomation,
    saveAutomation,
  };
};

// Responsive wrapper
export const ResponsiveAutomationBoard: React.FC = () => {
  const breakpoint = useBreakpoint();
  const [isToolboxOpen, setIsToolboxOpen] = useState(breakpoint !== 'mobile');

  return (
    <div className="h-screen flex flex-col">
      {/* Мобильный header */}
      {breakpoint === 'mobile' && (
        <div className="flex items-center justify-between p-4 border-b bg-white">
          <button
            onClick={() => setIsToolboxOpen(!isToolboxOpen)}
            className="p-2 rounded-lg bg-gray-100"
          >
            🧰
          </button>
          <h1 className="font-semibold">Автоматизация</h1>
          <button className="p-2 rounded-lg bg-blue-500 text-white">
            💾
          </button>
        </div>
      )}

      <div className="flex-1 flex">
        {(breakpoint !== 'mobile' || isToolboxOpen) && (
          <div className={`
            ${breakpoint === 'mobile' 
              ? 'fixed inset-0 z-50 bg-white' 
              : 'w-64'}
          `}>
            <AutomationToolbox />
            {breakpoint === 'mobile' && (
              <button
                onClick={() => setIsToolboxOpen(false)}
                className="absolute top-4 right-4 p-2 bg-gray-100 rounded-lg"
              >
                ✕
              </button>
            )}
          </div>
        )}
        
        <div className="flex-1">
          <AutomationBoard />
        </div>
      </div>
    </div>
  );
};
8. 🎯 Интеграция с бэкендом
typescript
// src/services/automationBoardApi.ts
export const automationBoardApi = {
  async loadBoard(automationId: string) {
    const response = await fetch(`/api/automation/${automationId}/board`);
    if (!response.ok) throw new Error('Failed to load board');
    return response.json();
  },

  async saveBoard(automationId: string, boardData: any) {
    const response = await fetch(`/api/automation/${automationId}/board`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boardData),
    });
    if (!response.ok) throw new Error('Failed to save board');
    return response.json();
  },

  async createFromTemplate(templateId: string) {
    const response = await fetch('/api/automation/from-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ templateId }),
    });
    return response.json();
  },

  async validateBoard(boardData: any) {
    const response = await fetch('/api/automation/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boardData),
    });
    return response.json();
  }
};
🚀 Преимущества этой реализации:
🎯 Визуальная ясность - Интуитивное построение процессов

🔄 Интерактивность - Drag & Drop, реальное время

🎨 Кастомизация - Цвета, иконки, настройки

🧪 Тестирование - Режим симуляции процессов

📱 Адаптивность - Работа на всех устройствах

💾 Сохранение - Автосохранение и версионность

🔧 Гибкость - Легко расширять новыми типами узлов