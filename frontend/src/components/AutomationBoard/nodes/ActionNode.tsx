import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const ActionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'send_email': return '📧';
      case 'create_task': return '✅';
      case 'update_status': return '🔄';
      case 'assign_user': return '👤';
      case 'call_webhook': return '🌐';
      default: return '🤖';
    }
  };

  return (
    <div className={`
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-van-gogh-chrome-green ring-2 ring-van-gogh-chrome-green/20' : 'border-van-gogh-chrome-green/60'}
      ${simulationStatus === 'active' ? 'border-green-400 ring-2 ring-green-400/20 bg-green-900/20' : 'bg-gray-800/80'}
    `}>
      {/* Входные точки */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-500"
      />

      <div className="flex items-center space-x-2 sm:space-x-3">
        <div className="text-base sm:text-lg">{getActionIcon(data.config?.actionType)}</div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-100 text-sm sm:text-base truncate">{data.label}</div>
          <div className="text-xs sm:text-sm text-gray-400 mt-1 hidden sm:block truncate">
            {data.config?.actionType && `Действие: ${data.config.actionType}`}
          </div>
        </div>
      </div>

      {/* Выходные точки */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-van-gogh-chrome-green"
      />
    </div>
  );
};
