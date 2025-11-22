import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const StageNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';

  return (
    <div className={`
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-van-gogh-ultramarine ring-2 ring-van-gogh-ultramarine/20' : 'border-gray-600'}
      ${simulationStatus === 'active' ? 'border-green-400 ring-2 ring-green-400/20 bg-green-900/20' : ''}
      ${data.color && simulationStatus !== 'active' ? 'bg-gray-800/80' : 'bg-gray-800/80'}
    `}>
      {/* Входные точки */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-500"
      />

      {/* Содержимое узла */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        <div
          className="w-2 h-2 sm:w-3 sm:h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: data.color }}
        />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-100 text-sm sm:text-base truncate">{data.label}</div>
          {data.description && (
            <div className="text-xs sm:text-sm text-gray-400 mt-1 hidden sm:block truncate">{data.description}</div>
          )}

          {/* Дополнительная информация - скрываем на очень маленьких экранах */}
          {data.robots && data.robots.length > 0 && (
            <div className="mt-1 sm:mt-2 text-xs text-gray-500">
              🤖 {data.robots.length}
            </div>
          )}
        </div>
      </div>

      {/* Выходные точки */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-500"
      />
    </div>
  );
};
