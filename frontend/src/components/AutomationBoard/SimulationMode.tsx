import React, { useState, useCallback, useMemo } from 'react';
import { useReactFlow } from 'reactflow';

interface SimulationModeProps {
  isActive: boolean;
  onToggle: () => void;
  onActiveNodesChange?: (activeNodes: Set<string>) => void;
}

interface SimulationStep {
  step: number;
  activeNodes: Set<string>;
  description: string;
  nodeDetails: Array<{
    id: string;
    label: string;
    type: string;
  }>;
}

export const SimulationMode: React.FC<SimulationModeProps> = ({
  isActive,
  onToggle,
  onActiveNodesChange
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [simulationHistory, setSimulationHistory] = useState<SimulationStep[]>([]);
  const { getNodes, getEdges } = useReactFlow();

  const startSimulation = useCallback(() => {
    setIsRunning(true);
    setCurrentStep(0);

    // Найти стартовые узлы (триггеры)
    const startNodes = getNodes().filter(node => node.type === 'trigger');
    const startNodeIds = new Set(startNodes.map(node => node.id));
    setActiveNodes(startNodeIds);
    onActiveNodesChange?.(startNodeIds);

    // Запустить пошаговое выполнение
    simulateStep(0, startNodeIds);
  }, [getNodes, onActiveNodesChange]);

  const simulateStep = useCallback((step: number, activeNodeIds: Set<string>) => {
    if (step > 20) { // Защита от бесконечного цикла
      setIsRunning(false);
      return;
    }

    setTimeout(() => {
      const edges = getEdges();
      const nodes = getNodes();

      // Найти следующие узлы, связанные с активными
      const nextActiveNodes = new Set<string>();

      activeNodeIds.forEach(nodeId => {
        const outgoingEdges = edges.filter(edge => edge.source === nodeId);
        outgoingEdges.forEach(edge => {
          // Для условий проверяем логику
          const sourceNode = nodes.find(n => n.id === nodeId);
          if (sourceNode?.type === 'condition') {
            // Имитируем случайный выбор для условий
            const targetIndex = Math.floor(Math.random() * outgoingEdges.length);
            nextActiveNodes.add(outgoingEdges[targetIndex].target);
          } else {
            nextActiveNodes.add(edge.target);
          }
        });
      });

      setActiveNodes(nextActiveNodes);
      onActiveNodesChange?.(nextActiveNodes);
      setCurrentStep(step + 1);

      if (nextActiveNodes.size > 0 && step < 10) {
        simulateStep(step + 1, nextActiveNodes);
      } else {
        setIsRunning(false);
      }
    }, 1500); // Задержка 1.5 секунды между шагами
  }, [getEdges, getNodes, onActiveNodesChange]);

  const stopSimulation = useCallback(() => {
    setIsRunning(false);
    setIsPaused(false);
    setCurrentStep(0);
    const emptySet = new Set<string>();
    setActiveNodes(emptySet);
    onActiveNodesChange?.(emptySet);
    setSimulationHistory([]);
  }, [onActiveNodesChange]);

  const resetSimulation = useCallback(() => {
    setIsRunning(false);
    setIsPaused(false);
    setCurrentStep(0);
    const emptySet = new Set<string>();
    setActiveNodes(emptySet);
    onActiveNodesChange?.(emptySet);
    setSimulationHistory([]);
  }, [onActiveNodesChange]);

  const pauseSimulation = useCallback(() => {
    setIsPaused(true);
    setIsRunning(false);
  }, []);

  const resumeSimulation = useCallback(() => {
    setIsPaused(false);
    setIsRunning(true);
    // Продолжить симуляцию с текущего шага
    const currentHistoryStep = simulationHistory[currentStep];
    if (currentHistoryStep) {
      simulateStep(currentStep, currentHistoryStep.activeNodes);
    }
  }, [simulationHistory, currentStep]);

  const nextStep = useCallback(() => {
    if (currentStep >= simulationHistory.length - 1) {
      // Вычислить следующий шаг
      const edges = getEdges();
      const nodes = getNodes();
      const nextActiveNodes = new Set<string>();

      activeNodes.forEach(nodeId => {
        const outgoingEdges = edges.filter(edge => edge.source === nodeId);
        outgoingEdges.forEach(edge => {
          const sourceNode = nodes.find(n => n.id === nodeId);
          if (sourceNode?.type === 'condition') {
            // Для условий выбираем первый путь (можно улучшить логику)
            nextActiveNodes.add(edge.target);
          } else {
            nextActiveNodes.add(edge.target);
          }
        });
      });

      if (nextActiveNodes.size > 0) {
        const nextStepNum = currentStep + 1;
        const stepDescription = `Шаг ${nextStepNum}: Переход к следующему узлу`;
        const nodeDetails = Array.from(nextActiveNodes).map(nodeId => {
          const node = nodes.find(n => n.id === nodeId);
          return {
            id: nodeId,
            label: node?.data?.label || nodeId,
            type: node?.type || 'unknown'
          };
        });

        const newStep: SimulationStep = {
          step: nextStepNum,
          activeNodes: nextActiveNodes,
          description: stepDescription,
          nodeDetails
        };

        setSimulationHistory(prev => [...prev, newStep]);
        setCurrentStep(nextStepNum);
        setActiveNodes(nextActiveNodes);
        onActiveNodesChange?.(nextActiveNodes);
      }
    } else {
      // Перейти к следующему сохраненному шагу
      const nextStepData = simulationHistory[currentStep + 1];
      setCurrentStep(currentStep + 1);
      setActiveNodes(nextStepData.activeNodes);
      onActiveNodesChange?.(nextStepData.activeNodes);
    }
  }, [currentStep, simulationHistory, activeNodes, getEdges, getNodes, onActiveNodesChange]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      const prevStepData = simulationHistory[currentStep - 1];
      setCurrentStep(currentStep - 1);
      setActiveNodes(prevStepData.activeNodes);
      onActiveNodesChange?.(prevStepData.activeNodes);
    }
  }, [currentStep, simulationHistory, onActiveNodesChange]);

  // Получить информацию о текущем шаге
  const currentStepInfo = useMemo(() => {
    if (simulationHistory.length === 0) return null;
    return simulationHistory[Math.min(currentStep, simulationHistory.length - 1)];
  }, [simulationHistory, currentStep]);

  if (!isActive) {
    return (
      <button
        onClick={onToggle}
        className="absolute top-4 left-4 z-10 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors shadow-lg"
      >
        🏃 Режим симуляции
      </button>
    );
  }

  return (
    <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-lg border border-gray-200 max-w-md">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Режим симуляции</h3>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>

      {/* Основные кнопки управления */}
      <div className="flex flex-wrap gap-2 mb-3">
        {!isRunning && !isPaused && (
          <button
            onClick={startSimulation}
            className="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"
          >
            ▶️ Запустить
          </button>
        )}

        {isRunning && (
          <button
            onClick={pauseSimulation}
            className="px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
          >
            ⏸️ Пауза
          </button>
        )}

        {isPaused && (
          <button
            onClick={resumeSimulation}
            className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
          >
            ▶️ Продолжить
          </button>
        )}

        {(isRunning || isPaused || currentStep > 0) && (
          <button
            onClick={stopSimulation}
            className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
          >
            ⏹️ Остановить
          </button>
        )}

        <button
          onClick={resetSimulation}
          className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm"
        >
          🔄 Сброс
        </button>
      </div>

      {/* Пошаговое управление */}
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={prevStep}
          disabled={currentStep === 0}
          className="px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          ⬅️ Назад
        </button>

        <span className="text-sm font-medium text-gray-900 min-w-[60px] text-center">
          Шаг {currentStep}
        </span>

        <button
          onClick={nextStep}
          disabled={isRunning}
          className="px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          Вперед ➡️
        </button>
      </div>

      {/* Информация о текущем шаге */}
      {currentStepInfo && (
        <div className="mb-3 p-2 bg-blue-50 rounded border">
          <div className="text-xs font-medium text-blue-900 mb-1">
            {currentStepInfo.description}
          </div>
          <div className="text-xs text-blue-700">
            Активные узлы: {currentStepInfo.nodeDetails.map(node => node.label).join(', ')}
          </div>
        </div>
      )}

      {/* Статус */}
      <div className="text-xs text-gray-500">
        {isRunning && "🏃 Симуляция выполняется..."}
        {isPaused && "⏸️ Симуляция на паузе"}
        {!isRunning && !isPaused && currentStep === 0 && "🎯 Готов к запуску"}
        {!isRunning && !isPaused && currentStep > 0 && `✅ Симуляция завершена (${currentStep} шагов)`}
      </div>

      <div className="mt-2 text-xs text-gray-400">
        💡 Активные узлы подсвечиваются зелёным цветом
      </div>
    </div>
  );
};
