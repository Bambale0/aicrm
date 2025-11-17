import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const TriggerNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';
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
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-red-500 ring-2 ring-red-200' : 'border-red-300'}
      ${simulationStatus === 'active' ? 'border-green-500 ring-2 ring-green-200 bg-green-50' : 'bg-red-50'}
    `}>
      <div className="flex items-center space-x-2 sm:space-x-3">
        <div className="text-base sm:text-lg">{getTriggerIcon(data.config?.type)}</div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 text-sm sm:text-base truncate">{data.label}</div>
          <div className="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block truncate">
            {data.config?.type && `Тип: ${data.config.type}`}
          </div>
        </div>
      </div>

      {/* Только выходная точка для триггера */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-red-400"
      />
    </div>
  );
};
