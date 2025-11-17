import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const StageNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';

  return (
    <div className={`
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
      ${simulationStatus === 'active' ? 'border-green-500 ring-2 ring-green-200 bg-green-50' : ''}
      ${data.color && simulationStatus !== 'active' ? `bg-${data.color}-50 border-${data.color}-300` : 'bg-white'}
    `}>
      {/* Входные точки */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-400"
      />

      {/* Содержимое узла */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        <div
          className="w-2 h-2 sm:w-3 sm:h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: data.color }}
        />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 text-sm sm:text-base truncate">{data.label}</div>
          {data.description && (
            <div className="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block truncate">{data.description}</div>
          )}

          {/* Дополнительная информация - скрываем на очень маленьких экранах */}
          {data.robots && data.robots.length > 0 && (
            <div className="mt-1 sm:mt-2 text-xs text-gray-600">
              🤖 {data.robots.length}
            </div>
          )}
        </div>
      </div>

      {/* Выходные точки */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-400"
      />
    </div>
  );
};
