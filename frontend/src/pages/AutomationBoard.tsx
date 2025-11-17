import React, { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { AutomationBoard } from '../components/AutomationBoard/AutomationBoard';
import { ProcessData } from '../types/automation-board';

const AutomationBoardPage: React.FC = () => {
  const [process, setProcess] = useState<ProcessData | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Загрузка данных процесса (пример)
    const loadProcess = async () => {
      try {
        // TODO: Заменить на реальный API вызов
        const mockProcess: ProcessData = {
          id: 1,
          name: "Процесс заказа",
          stages: [
            { id: 1, name: "Новый заказ", order_index: 0 },
            { id: 2, name: "В производстве", order_index: 1 },
            { id: 3, name: "Готов", order_index: 2 }
          ],
          triggers: [
            { id: 1, event_type: "stage_completed", source_stage_id: 1, target_stage_id: 2 },
            { id: 2, event_type: "stage_completed", source_stage_id: 2, target_stage_id: 3 }
          ]
        };

        setProcess(mockProcess);
      } catch (error) {
        console.error('Failed to load process:', error);
      } finally {
        setLoading(false);
      }
    };

    loadProcess();
  }, []);

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
