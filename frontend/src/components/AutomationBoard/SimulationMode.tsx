import React, { useCallback, useMemo, useState } from 'react';
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
  }, [simulationHistory, currentStep, simulateStep]);

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
        className="absolute top-4 left-4 z-10 bg-van-gogh-ultramarine text-white px-4 py-2 rounded-lg hover:bg-van-gogh-vermilion transition-colors shadow-lg"
      >
        🏃 Режим симуляции
      </button>
    );
  }

  return (
    <div className="absolute top-4 left-4 z-10 card p-4 max-w-md">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-van-gogh-starry-night-blue">Режим симуляции</h3>
        <button
          onClick={onToggle}
          className="p-2 text-gray-400 hover:text-van-gogh-ultramarine rounded-lg hover:bg-van-gogh-ultramarine/10 transition-colors"
          aria-label="Закрыть"
        >
          ✕
        </button>
      </div>

      {/* Основные кнопки управления */}
      <div className="flex flex-wrap gap-2 mb-3">
        {!isRunning && !isPaused && (
          <button
            onClick={startSimulation}
            className="px-3 py-2 bg-van-gogh-vermilion text-white rounded-lg hover:bg-van-gogh-vermilion/80 transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl text-sm font-medium"
          >
            ▶️ Запустить
          </button>
        )}

        {isRunning && (
          <button
            onClick={pauseSimulation}
            className="px-3 py-2 bg-van-gogh-sunflower text-white rounded-lg hover:bg-van-gogh-sunflower/80 transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl text-sm font-medium"
          >
            ⏸️ Пауза
          </button>
        )}

        {isPaused && (
          <button
            onClick={resumeSimulation}
            className="px-3 py-2 bg-van-gogh-ultramarine text-white rounded-lg hover:bg-van-gogh-ultramarine/80 transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl text-sm font-medium"
          >
            ▶️ Продолжить
          </button>
        )}

        {(isRunning || isPaused || currentStep > 0) && (
          <button
            onClick={stopSimulation}
            className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl text-sm font-medium"
          >
            ⏹️ Остановить
          </button>
        )}

        <button
          onClick={resetSimulation}
          className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl text-sm font-medium"
        >
          🔄 Сброс
        </button>
      </div>

      {/* Пошаговое управление */}
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={prevStep}
          disabled={currentStep === 0}
          className="px-2 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-colors"
        >
          ⬅️ Назад
        </button>

        <span className="text-sm font-medium text-van-gogh-starry-night-blue min-w-[60px] text-center">
          Шаг {currentStep}
        </span>

        <button
          onClick={nextStep}
          disabled={isRunning}
          className="px-2 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-colors"
        >
          Вперед ➡️
        </button>
      </div>

      {/* Информация о текущем шаге */}
      {currentStepInfo && (
        <div className="mb-3 p-2 bg-van-gogh-ultramarine/10 rounded border border-van-gogh-ultramarine/20">
          <div className="text-xs font-medium text-van-gogh-ultramarine mb-1">
            {currentStepInfo.description}
          </div>
          <div className="text-xs text-gray-300">
            Активные узлы: {currentStepInfo.nodeDetails.map(node => node.label).join(', ')}
          </div>
        </div>
      )}

      {/* Статус */}
      <div className="text-xs text-gray-400">
        {isRunning && "🏃 Симуляция выполняется..."}
        {isPaused && "⏸️ Симуляция на паузе"}
        {!isRunning && !isPaused && currentStep === 0 && "🎯 Готов к запуску"}
        {!isRunning && !isPaused && currentStep > 0 && `✅ Симуляция завершена (${currentStep} шагов)`}
      </div>

      <div className="mt-2 text-xs text-gray-500">
        💡 Активные узлы подсвечиваются зелёным цветом
      </div>
    </div>
  );
};
