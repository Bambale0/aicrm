import React from 'react';

const toolboxItems = [
  {
    type: 'trigger',
    label: 'Триггер',
    description: 'Запускает процесс автоматизации',
    icon: '⚡',
    color: '#ef4444',
    examples: ['Новый заказ', 'Новый клиент', 'Сообщение']
  },
  {
    type: 'stage',
    label: 'Стадия',
    description: 'Этап процесса',
    icon: '📋',
    color: '#3b82f6',
    examples: ['Обработка', 'Производство', 'Контроль качества']
  },
  {
    type: 'action',
    label: 'Действие',
    description: 'Автоматическое действие',
    icon: '🤖',
    color: '#10b981',
    examples: ['Отправить email', 'Создать задачу', 'Обновить статус']
  },
  {
    type: 'condition',
    label: 'Условие',
    description: 'Проверка условия',
    icon: '❓',
    color: '#f59e0b',
    examples: ['Если сумма > 10000', 'Если VIP клиент']
  },
  {
    type: 'delay',
    label: 'Задержка',
    description: 'Пауза в процессе',
    icon: '⏰',
    color: '#8b5cf6',
    examples: ['Ждать 2 часа', 'Ждать до понедельника']
  }
];

export const AutomationToolbox: React.FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Элементы автоматизации</h2>
        <p className="text-sm text-gray-500 mt-1">Перетащите на доску</p>
      </div>

      <div className="p-4 space-y-3">
        {toolboxItems.map((item) => (
          <div
            key={item.type}
            className="border border-gray-200 rounded-lg p-3 cursor-move hover:shadow-md transition-shadow bg-white"
            onDragStart={(e) => onDragStart(e, item.type)}
            draggable
          >
            <div className="flex items-start space-x-3">
              <div
                className="text-xl flex-shrink-0"
                style={{ color: item.color }}
              >
                {item.icon}
              </div>

              <div className="flex-1">
                <div className="font-medium text-gray-900">{item.label}</div>
                <div className="text-sm text-gray-500 mt-1">{item.description}</div>

                <div className="mt-2">
                  <div className="text-xs text-gray-400">Примеры:</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {item.examples.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Шаблоны процессов */}
      <div className="p-4 border-t border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3">Готовые шаблоны</h3>
        <div className="space-y-2">
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            🛒 Процесс заказа
          </button>
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            👤 Онбординг клиента
          </button>
          <button className="w-full text-left p-2 text-sm border border-gray-200 rounded hover:bg-gray-50">
            📧 Email кампания
          </button>
        </div>
      </div>
    </div>
  );
};
