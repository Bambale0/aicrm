import React, { useState, useEffect } from 'react';
import { automationApi, Process, Stage, Trigger, Robot } from '../../services/automationApi.ts';
import {
  PlusIcon,
  Cog6ToothIcon,
  BoltIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  CpuChipIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface WorkflowNode {
  id: string;
  type: 'stage' | 'trigger' | 'robot';
  data: Stage | Trigger | Robot;
  position: { x: number; y: number };
}

interface WorkflowConnection {
  id: string;
  sourceId: string;
  targetId: string;
  type: 'trigger_to_stage' | 'stage_to_robot';
}

interface WorkflowDesignerProps {
  processId?: number;
  onSave?: (workflow: { process: Process; stages: Stage[]; triggers: Trigger[]; robots: Robot[] }) => void;
  onCancel?: () => void;
}

export default function WorkflowDesigner({ processId, onSave, onCancel }: WorkflowDesignerProps) {
  const [process, setProcess] = useState<Process | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [robots, setRobots] = useState<Robot[]>([]);
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [connections, setConnections] = useState<WorkflowConnection[]>([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showAIGenerator, setShowAIGenerator] = useState(false);
  const [aiDescription, setAiDescription] = useState('');
  const [entityType, setEntityType] = useState('order');

  // Load existing process if processId provided
  useEffect(() => {
    if (processId) {
      loadProcess(processId);
    } else {
      // Create new process
      setProcess({
        id: 0,
        name: 'Новый процесс',
        description: '',
        entity_type: 'order',
        is_active: true,
        created_at: new Date().toISOString()
      });
    }
  }, [processId]);

  const loadProcess = async (id: number) => {
    try {
      const [processData, stagesData, triggersData, robotsData] = await Promise.all([
        automationApi.getProcess(id),
        automationApi.getStages({ process_id: id }),
        automationApi.getTriggers(),
        automationApi.getRobots()
      ]);

      setProcess(processData);
      setStages(stagesData);
      setTriggers(triggersData.filter(t => stagesData.some(s => s.id === t.target_stage_id)));
      setRobots(robotsData.filter(r => stagesData.some(s => s.id === r.stage_id)));

      // Create nodes from data
      const workflowNodes: WorkflowNode[] = [];
      const workflowConnections: WorkflowConnection[] = [];

      // Add stage nodes
      stagesData.forEach((stage, index) => {
        workflowNodes.push({
          id: `stage-${stage.id}`,
          type: 'stage',
          data: stage,
          position: { x: 100 + (index * 300), y: 200 }
        });
      });

      // Add trigger nodes
      triggersData.forEach((trigger, index) => {
        workflowNodes.push({
          id: `trigger-${trigger.id}`,
          type: 'trigger',
          data: trigger,
          position: { x: 50 + (index * 200), y: 50 }
        });

        // Connect trigger to target stage
        workflowConnections.push({
          id: `conn-${trigger.id}`,
          sourceId: `trigger-${trigger.id}`,
          targetId: `stage-${trigger.target_stage_id}`,
          type: 'trigger_to_stage'
        });
      });

      // Add robot nodes
      robotsData.forEach((robot, index) => {
        const stageNode = workflowNodes.find(n => n.id === `stage-${robot.stage_id}`);
        if (stageNode) {
          workflowNodes.push({
            id: `robot-${robot.id}`,
            type: 'robot',
            data: robot,
            position: { x: stageNode.position.x, y: stageNode.position.y + 150 + (index * 100) }
          });

          workflowConnections.push({
            id: `robot-conn-${robot.id}`,
            sourceId: `stage-${robot.stage_id}`,
            targetId: `robot-${robot.id}`,
            type: 'stage_to_robot'
          });
        }
      });

      setNodes(workflowNodes);
      setConnections(workflowConnections);
    } catch (error) {
      console.error('Failed to load process:', error);
    }
  };

  const generateWithAI = async () => {
    if (!aiDescription.trim()) return;

    setIsGenerating(true);
    try {
      const result = await automationApi.generateAutomationChain({
        description: aiDescription,
        entity_type: entityType,
        complexity_level: 'medium'
      });

      if (result.success && result.process && result.stages) {
        setProcess(result.process);
        setStages(result.stages);
        setTriggers(result.triggers || []);
        setRobots(result.robots || []);

        // Create nodes from AI-generated data
        const workflowNodes: WorkflowNode[] = [];
        const workflowConnections: WorkflowConnection[] = [];

        result.stages.forEach((stage, index) => {
          workflowNodes.push({
            id: `stage-${stage.id}`,
            type: 'stage',
            data: stage,
            position: { x: 100 + (index * 300), y: 200 }
          });
        });

        if (result.triggers) {
          result.triggers.forEach((trigger, index) => {
            workflowNodes.push({
              id: `trigger-${trigger.id}`,
              type: 'trigger',
              data: trigger,
              position: { x: 50 + (index * 200), y: 50 }
            });

            workflowConnections.push({
              id: `conn-${trigger.id}`,
              sourceId: `trigger-${trigger.id}`,
              targetId: `stage-${trigger.target_stage_id}`,
              type: 'trigger_to_stage'
            });
          });
        }

        if (result.robots) {
          result.robots.forEach((robot, index) => {
            const stageNode = workflowNodes.find(n => n.id === `stage-${robot.stage_id}`);
            if (stageNode) {
              workflowNodes.push({
                id: `robot-${robot.id}`,
                type: 'robot',
                data: robot,
                position: { x: stageNode.position.x, y: stageNode.position.y + 150 + (index * 100) }
              });

              workflowConnections.push({
                id: `robot-conn-${robot.id}`,
                sourceId: `stage-${robot.stage_id}`,
                targetId: `robot-${robot.id}`,
                type: 'stage_to_robot'
              });
            }
          });
        }

        setNodes(workflowNodes);
        setConnections(workflowConnections);
        setShowAIGenerator(false);
        setAiDescription('');
      }
    } catch (error) {
      console.error('Failed to generate with AI:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const addStage = () => {
    const newStage: Omit<Stage, 'id' | 'created_at'> = {
      name: 'Новая стадия',
      description: '',
      entity_type: process?.entity_type || 'order',
      process_id: process?.id || 0,
      order_index: stages.length,
      color: '#3B82F6',
      is_active: true
    };

    automationApi.createStage(newStage).then(stage => {
      setStages([...stages, stage]);
      const newNode: WorkflowNode = {
        id: `stage-${stage.id}`,
        type: 'stage',
        data: stage,
        position: { x: 100 + (stages.length * 300), y: 200 }
      };
      setNodes([...nodes, newNode]);
    });
  };

  const addTrigger = () => {
    if (stages.length === 0) return;

    const newTrigger: Omit<Trigger, 'id' | 'created_at'> = {
      name: 'Новый триггер',
      description: '',
      entity_type: process?.entity_type || 'order',
      event_type: 'order_created',
      target_stage_id: stages[0].id,
      is_active: true
    };

    automationApi.createTrigger(newTrigger).then(trigger => {
      setTriggers([...triggers, trigger]);
      const newNode: WorkflowNode = {
        id: `trigger-${trigger.id}`,
        type: 'trigger',
        data: trigger,
        position: { x: 50 + (triggers.length * 200), y: 50 }
      };
      setNodes([...nodes, newNode]);

      // Add connection
      const newConnection: WorkflowConnection = {
        id: `conn-${trigger.id}`,
        sourceId: `trigger-${trigger.id}`,
        targetId: `stage-${trigger.target_stage_id}`,
        type: 'trigger_to_stage'
      };
      setConnections([...connections, newConnection]);
    });
  };

  const addRobot = (stageId: number) => {
    const newRobot: Omit<Robot, 'id' | 'created_at'> = {
      name: 'Новый робот',
      description: '',
      entity_type: process?.entity_type || 'order',
      stage_id: stageId,
      is_active: true
    };

    automationApi.createRobot(newRobot).then(robot => {
      setRobots([...robots, robot]);
      const stageNode = nodes.find(n => n.id === `stage-${stageId}`);
      if (stageNode) {
        const robotNodes = nodes.filter(n => n.type === 'robot' && (n.data as Robot).stage_id === stageId);
        const newNode: WorkflowNode = {
          id: `robot-${robot.id}`,
          type: 'robot',
          data: robot,
          position: { x: stageNode.position.x, y: stageNode.position.y + 150 + (robotNodes.length * 100) }
        };
        setNodes([...nodes, newNode]);

        // Add connection
        const newConnection: WorkflowConnection = {
          id: `robot-conn-${robot.id}`,
          sourceId: `stage-${stageId}`,
          targetId: `robot-${robot.id}`,
          type: 'stage_to_robot'
        };
        setConnections([...connections, newConnection]);
      }
    });
  };

  const deleteNode = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    // Remove from API and state
    if (node.type === 'stage') {
      automationApi.deleteStage((node.data as Stage).id);
      setStages(stages.filter(s => s.id !== (node.data as Stage).id));
    } else if (node.type === 'trigger') {
      automationApi.deleteTrigger((node.data as Trigger).id);
      setTriggers(triggers.filter(t => t.id !== (node.data as Trigger).id));
    } else if (node.type === 'robot') {
      automationApi.deleteRobot((node.data as Robot).id);
      setRobots(robots.filter(r => r.id !== (node.data as Robot).id));
    }

    // Remove connections
    setConnections(connections.filter(c => c.sourceId !== nodeId && c.targetId !== nodeId));
    setNodes(nodes.filter(n => n.id !== nodeId));
  };

  const saveWorkflow = () => {
    if (onSave && process) {
      onSave({
        process,
        stages,
        triggers,
        robots
      });
    }
  };

  const renderNode = (node: WorkflowNode) => {
    const isSelected = selectedNode?.id === node.id;

    if (node.type === 'stage') {
      const stage = node.data as Stage;
      return (
        <div
          key={node.id}
          className={`absolute p-4 rounded-lg border-2 cursor-pointer transition-all ${
            isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-blue-300'
          }`}
          style={{
            left: node.position.x,
            top: node.position.y,
            backgroundColor: stage.color + '20',
            borderColor: stage.color
          }}
          onClick={() => setSelectedNode(node)}
        >
          <div className="flex items-center space-x-2">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: stage.color }}
            />
            <h4 className="font-medium text-gray-900">{stage.name}</h4>
          </div>
          <p className="text-sm text-gray-600 mt-1">{stage.description}</p>
          <div className="flex space-x-1 mt-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                addRobot(stage.id);
              }}
              className="p-1 text-gray-400 hover:text-blue-600"
              title="Добавить робота"
            >
              <Cog6ToothIcon className="w-4 h-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteNode(node.id);
              }}
              className="p-1 text-gray-400 hover:text-red-600"
              title="Удалить"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      );
    }

    if (node.type === 'trigger') {
      const trigger = node.data as Trigger;
      return (
        <div
          key={node.id}
          className={`absolute p-3 rounded-lg border-2 cursor-pointer transition-all ${
            isSelected ? 'border-green-500 bg-green-50' : 'border-gray-300 bg-white hover:border-green-300'
          }`}
          style={{ left: node.position.x, top: node.position.y }}
          onClick={() => setSelectedNode(node)}
        >
          <div className="flex items-center space-x-2">
            <BoltIcon className="w-4 h-4 text-yellow-500" />
            <h4 className="font-medium text-gray-900">{trigger.name}</h4>
          </div>
          <p className="text-sm text-gray-600">{trigger.event_type}</p>
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteNode(node.id);
            }}
            className="absolute top-1 right-1 p-1 text-gray-400 hover:text-red-600"
            title="Удалить"
          >
            <TrashIcon className="w-3 h-3" />
          </button>
        </div>
      );
    }

    if (node.type === 'robot') {
      const robot = node.data as Robot;
      return (
        <div
          key={node.id}
          className={`absolute p-3 rounded-lg border-2 cursor-pointer transition-all ${
            isSelected ? 'border-purple-500 bg-purple-50' : 'border-gray-300 bg-white hover:border-purple-300'
          }`}
          style={{ left: node.position.x, top: node.position.y }}
          onClick={() => setSelectedNode(node)}
        >
          <div className="flex items-center space-x-2">
            <CpuChipIcon className="w-4 h-4 text-purple-500" />
            <h4 className="font-medium text-gray-900">{robot.name}</h4>
          </div>
          <p className="text-sm text-gray-600">{robot.description}</p>
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteNode(node.id);
            }}
            className="absolute top-1 right-1 p-1 text-gray-400 hover:text-red-600"
            title="Удалить"
          >
            <TrashIcon className="w-3 h-3" />
          </button>
        </div>
      );
    }

    return null;
  };

  const renderConnection = (connection: WorkflowConnection) => {
    const sourceNode = nodes.find(n => n.id === connection.sourceId);
    const targetNode = nodes.find(n => n.id === connection.targetId);

    if (!sourceNode || !targetNode) return null;

    const sourceX = sourceNode.position.x + 100; // Approximate center
    const sourceY = sourceNode.position.y + (sourceNode.type === 'stage' ? 60 : 40);
    const targetX = targetNode.position.x + 100;
    const targetY = targetNode.position.y;

    return (
      <svg
        key={connection.id}
        className="absolute top-0 left-0 pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      >
        <defs>
          <marker
            id={`arrowhead-${connection.id}`}
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill={connection.type === 'trigger_to_stage' ? '#10B981' : '#8B5CF6'}
            />
          </marker>
        </defs>
        <path
          d={`M ${sourceX} ${sourceY} L ${targetX} ${targetY}`}
          stroke={connection.type === 'trigger_to_stage' ? '#10B981' : '#8B5CF6'}
          strokeWidth="2"
          fill="none"
          markerEnd={`url(#arrowhead-${connection.id})`}
        />
      </svg>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {process?.name || 'Конструктор автоматизации'}
          </h2>
          <p className="text-sm text-gray-600">
            Создайте процесс автоматизации с помощью drag-and-drop
          </p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setShowAIGenerator(true)}
            className="btn-secondary flex items-center"
          >
            <LightBulbIcon className="w-4 h-4 mr-2" />
            Сгенерировать ИИ
          </button>

          <button
            onClick={addTrigger}
            className="btn-secondary flex items-center"
            disabled={stages.length === 0}
          >
            <BoltIcon className="w-4 h-4 mr-2" />
            Добавить триггер
          </button>

          <button
            onClick={addStage}
            className="btn-secondary flex items-center"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Добавить стадию
          </button>

          <button
            onClick={saveWorkflow}
            className="btn-primary flex items-center"
          >
            <PlayIcon className="w-4 h-4 mr-2" />
            Сохранить
          </button>

          {onCancel && (
            <button
              onClick={onCancel}
              className="btn-secondary flex items-center"
            >
              <StopIcon className="w-4 h-4 mr-2" />
              Отмена
            </button>
          )}
        </div>
      </div>

      {/* AI Generator Modal */}
      {showAIGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Генерация автоматизации с ИИ
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип сущности
                </label>
                <select
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value)}
                  className="input-field"
                >
                  <option value="order">Заказы</option>
                  <option value="customer">Клиенты</option>
                  <option value="task">Задачи</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Описание процесса
                </label>
                <textarea
                  value={aiDescription}
                  onChange={(e) => setAiDescription(e.target.value)}
                  placeholder="Опишите бизнес-процесс, который нужно автоматизировать..."
                  className="input-field h-24 resize-none"
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowAIGenerator(false)}
                  className="btn-secondary"
                >
                  Отмена
                </button>
                <button
                  onClick={generateWithAI}
                  disabled={isGenerating || !aiDescription.trim()}
                  className="btn-primary flex items-center"
                >
                  {isGenerating && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />}
                  <LightBulbIcon className="w-4 h-4 mr-2" />
                  {isGenerating ? 'Генерация...' : 'Сгенерировать'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Canvas */}
      <div className="flex-1 relative overflow-auto bg-gray-50">
        <div className="relative w-full h-full min-h-[600px]">
          {/* Render connections */}
          {connections.map(renderConnection)}

          {/* Render nodes */}
          {nodes.map(renderNode)}
        </div>
      </div>

      {/* Properties Panel */}
      {selectedNode && (
        <div className="border-t p-4 bg-white">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Свойства {selectedNode.type === 'stage' ? 'стадии' : selectedNode.type === 'trigger' ? 'триггера' : 'робота'}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название
              </label>
              <input
                type="text"
                value={selectedNode.data.name}
                onChange={(e) => {
                  const updatedData = { ...selectedNode.data, name: e.target.value };
                  // Update in API and state
                  if (selectedNode.type === 'stage') {
                    automationApi.updateStage((selectedNode.data as Stage).id, { name: e.target.value });
                    setStages(stages.map(s => s.id === (selectedNode.data as Stage).id ? { ...s, name: e.target.value } : s));
                  } else if (selectedNode.type === 'trigger') {
                    automationApi.updateTrigger((selectedNode.data as Trigger).id, { name: e.target.value });
                    setTriggers(triggers.map(t => t.id === (selectedNode.data as Trigger).id ? { ...t, name: e.target.value } : t));
                  } else if (selectedNode.type === 'robot') {
                    automationApi.updateRobot((selectedNode.data as Robot).id, { name: e.target.value });
                    setRobots(robots.map(r => r.id === (selectedNode.data as Robot).id ? { ...r, name: e.target.value } : r));
                  }

                  setNodes(nodes.map(n => n.id === selectedNode.id ? { ...n, data: updatedData } : n));
                }}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Описание
              </label>
              <textarea
                value={selectedNode.data.description || ''}
                onChange={(e) => {
                  const updatedData = { ...selectedNode.data, description: e.target.value };
                  // Update in API and state
                  if (selectedNode.type === 'stage') {
                    automationApi.updateStage((selectedNode.data as Stage).id, { description: e.target.value });
                    setStages(stages.map(s => s.id === (selectedNode.data as Stage).id ? { ...s, description: e.target.value } : s));
                  } else if (selectedNode.type === 'trigger') {
                    automationApi.updateTrigger((selectedNode.data as Trigger).id, { description: e.target.value });
                    setTriggers(triggers.map(t => t.id === (selectedNode.data as Trigger).id ? { ...t, description: e.target.value } : t));
                  } else if (selectedNode.type === 'robot') {
                    automationApi.updateRobot((selectedNode.data as Robot).id, { description: e.target.value });
                    setRobots(robots.map(r => r.id === (selectedNode.data as Robot).id ? { ...r, description: e.target.value } : r));
                  }

                  setNodes(nodes.map(n => n.id === selectedNode.id ? { ...n, data: updatedData } : n));
                }}
                className="input-field h-20 resize-none"
              />
            </div>

            {selectedNode.type === 'stage' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Цвет
                </label>
                <input
                  type="color"
                  value={(selectedNode.data as Stage).color || '#3B82F6'}
                  onChange={(e) => {
                    automationApi.updateStage((selectedNode.data as Stage).id, { color: e.target.value });
                    const updatedData = { ...selectedNode.data, color: e.target.value };
                    setStages(stages.map(s => s.id === (selectedNode.data as Stage).id ? { ...s, color: e.target.value } : s));
                    setNodes(nodes.map(n => n.id === selectedNode.id ? { ...n, data: updatedData } : n));
                  }}
                  className="input-field h-10"
                />
              </div>
            )}

            {selectedNode.type === 'trigger' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип события
                </label>
                <select
                  value={(selectedNode.data as Trigger).event_type}
                  onChange={(e) => {
                    automationApi.updateTrigger((selectedNode.data as Trigger).id, { event_type: e.target.value });
                    const updatedData = { ...selectedNode.data, event_type: e.target.value };
                    setTriggers(triggers.map(t => t.id === (selectedNode.data as Trigger).id ? { ...t, event_type: e.target.value } : t));
                    setNodes(nodes.map(n => n.id === selectedNode.id ? { ...n, data: updatedData } : n));
                  }}
                  className="input-field"
                >
                  <option value="order_created">Создание заказа</option>
                  <option value="order_completed">Завершение заказа</option>
                  <option value="customer_created">Создание клиента</option>
                  <option value="task_created">Создание задачи</option>
                  <option value="message_received">Получение сообщения</option>
                </select>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
