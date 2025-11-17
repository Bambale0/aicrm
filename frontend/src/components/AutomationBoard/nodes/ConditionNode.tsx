import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const ConditionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';

  return (
    <div className={`
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-yellow-500 ring-2 ring-yellow-200' : 'border-yellow-300'}
      ${simulationStatus === 'active' ? 'border-green-500 ring-2 ring-green-200 bg-green-50' : 'bg-yellow-50'}
    `}>
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-400"
      />

      <div className="flex items-center space-x-2 sm:space-x-3">
        <div className="text-base sm:text-lg">❓</div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 text-sm sm:text-base truncate">{data.label}</div>
          {data.config?.condition && (
            <div className="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block truncate">
              Условие: {data.config.condition}
            </div>
          )}
        </div>
      </div>

      {/* Два выхода для условий Да/Нет */}
      <div className="flex justify-between mt-1 sm:mt-2">
        <Handle
          type="source"
          position={Position.Bottom}
          id="true"
          className="w-2 h-2 sm:w-3 sm:h-3 bg-green-400"
        >
          <div className="text-xs text-green-600 -mt-3 sm:-mt-4 -ml-1 sm:-ml-2">Да</div>
        </Handle>
        <Handle
          type="source"
          position={Position.Bottom}
          id="false"
          className="w-2 h-2 sm:w-3 sm:h-3 bg-red-400"
        >
          <div className="text-xs text-red-600 -mt-3 sm:-mt-4 -ml-1 sm:-ml-2">Нет</div>
        </Handle>
      </div>
    </div>
  );
};
