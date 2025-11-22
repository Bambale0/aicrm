import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { AutomationBoard } from '../components/AutomationBoard/AutomationBoard';
import { ProcessData } from '../types/automation-board';
import { automationApi } from '../services/automationApi';

const AutomationBoardPage: React.FC = () => {
  const { processId } = useParams<{ processId: string }>();
  const [process, setProcess] = useState<ProcessData | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProcess = async () => {
      try {
        if (!processId) {
          console.error('Process ID not provided');
          return;
        }

        const processIdNum = parseInt(processId);

        // Сначала получаем информацию о процессе
        const processInfo = await automationApi.getProcess(processIdNum);

        // Затем получаем этапы и триггеры параллельно
        const [stages, triggers] = await Promise.all([
          automationApi.getStages({ process_id: processIdNum }),
          automationApi.getTriggers({ entity_type: processInfo.entity_type })
        ]);

        // Формируем ProcessData для компонента
        const processData: ProcessData = {
          id: processInfo.id,
          name: processInfo.name,
          stages: stages.map(stage => ({
            id: stage.id,
            name: stage.name,
            order_index: stage.order_index
          })),
          triggers: triggers
            .filter(trigger => trigger.target_stage_id && stages.some(s => s.id === trigger.target_stage_id))
            .map(trigger => ({
              id: trigger.id,
              event_type: trigger.event_type,
              source_stage_id: stages.find(s => s.order_index === 0)?.id || 0, // Предполагаем, что триггер идет от первого этапа
              target_stage_id: trigger.target_stage_id
            }))
        };

        setProcess(processData);
      } catch (error) {
        console.error('Failed to load process:', error);
        alert('Ошибка при загрузке процесса автоматизации');
      } finally {
        setLoading(false);
      }
    };

    loadProcess();
  }, [processId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Загрузка доски автоматизации...</div>
      </div>
    );
  }

  return (
    <div className="h-screen">
      <ReactFlowProvider>
        <AutomationBoard process={process} automationId="1" />
      </ReactFlowProvider>
    </div>
  );
};

export default AutomationBoardPage;
