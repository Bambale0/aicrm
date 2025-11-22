import React from 'react';
import { Node, Edge } from 'reactflow';

interface AutomationPropertiesProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onUpdate: (data: any) => void;
}

export const AutomationProperties: React.FC<AutomationPropertiesProps> = ({
  selectedNode,
  selectedEdge,
  onUpdate,
}) => {
  if (!selectedNode && !selectedEdge) {
    return (
      <div className="p-6 text-center text-gray-400">
        <div className="text-4xl mb-2">🎯</div>
        <p>Выберите элемент на доске для настройки</p>
      </div>
    );
  }

  if (selectedNode) {
    return <NodeProperties node={selectedNode} onUpdate={onUpdate} />;
  }

  if (selectedEdge) {
    return <EdgeProperties edge={selectedEdge} onUpdate={onUpdate} />;
  }

  return null;
};

const NodeProperties: React.FC<{ node: Node; onUpdate: (data: any) => void }> = ({
  node,
  onUpdate,
}) => {
  const [formData, setFormData] = React.useState(node.data);

  const handleChange = (field: string, value: any) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    onUpdate(newData);
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-medium text-van-gogh-starry-night-blue mb-4">Настройки узла</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Название
          </label>
          <input
            type="text"
            value={formData.label || ''}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Описание
          </label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
          />
        </div>

        {/* Динамические поля в зависимости от типа узла */}
        {node.type === 'trigger' && (
          <TriggerConfig
            config={formData.config}
            onChange={(config) => handleChange('config', config)}
          />
        )}

        {node.type === 'stage' && (
          <StageConfig
            config={formData.config}
            onChange={(config) => handleChange('config', config)}
          />
        )}

        {node.type === 'action' && (
          <ActionConfig
            config={formData.config}
            onChange={(config) => handleChange('config', config)}
          />
        )}

        {node.type === 'condition' && (
          <ConditionConfig
            config={formData.config}
            onChange={(config) => handleChange('config', config)}
          />
        )}

        {/* Цвет узла */}
        <div>
          <label className="block text-sm font-medium text-van-gogh-starry-night-blue mb-2">
            Цвет узла
          </label>
          <div className="flex flex-wrap gap-3">
            {[
              { color: '#ef4444', name: 'Красный' },
              { color: '#3b82f6', name: 'Синий' },
              { color: '#10b981', name: 'Зеленый' },
              { color: '#f59e0b', name: 'Оранжевый' },
              { color: '#8b5cf6', name: 'Фиолетовый' },
              { color: '#ec4899', name: 'Розовый' },
              { color: '#6366f1', name: 'Индиго' },
              { color: '#14b8a6', name: 'Бирюзовый' }
            ].map(({ color, name }) => (
              <button
                key={color}
                className={`w-10 h-10 rounded-full border-2 transition-all duration-200 hover:scale-110 ${
                  formData.color === color
                    ? 'border-van-gogh-ultramarine shadow-lg shadow-van-gogh-ultramarine/30'
                    : 'border-gray-600 hover:border-gray-400'
                }`}
                style={{ backgroundColor: color }}
                onClick={() => handleChange('color', color)}
                title={name}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const TriggerConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  const triggerTypes = [
    { value: 'order_created', label: 'Создан заказ', icon: '🛒' },
    { value: 'customer_created', label: 'Создан клиент', icon: '👤' },
    { value: 'task_completed', label: 'Завершена задача', icon: '✅' },
    { value: 'message_received', label: 'Получено сообщение', icon: '💬' },
    { value: 'status_changed', label: 'Изменен статус', icon: '🔄' },
  ];

  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        Тип триггера
      </label>
      <select
        value={config?.type || ''}
        onChange={(e) => onChange({ ...config, type: e.target.value })}
        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
      >
        <option value="">Выберите тип триггера</option>
        {triggerTypes.map((type) => (
          <option key={type.value} value={type.value}>
            {type.icon} {type.label}
          </option>
        ))}
      </select>
    </div>
  );
};

const ActionConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  const actionTypes = [
    { value: 'send_email', label: 'Отправить email', icon: '📧' },
    { value: 'create_task', label: 'Создать задачу', icon: '✅' },
    { value: 'update_status', label: 'Обновить статус', icon: '🔄' },
    { value: 'assign_user', label: 'Назначить пользователя', icon: '👤' },
    { value: 'call_webhook', label: 'Вызвать webhook', icon: '🌐' },
  ];

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Тип действия
        </label>
        <select
          value={config?.actionType || ''}
          onChange={(e) => onChange({ ...config, actionType: e.target.value })}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
        >
          <option value="">Выберите действие</option>
          {actionTypes.map((action) => (
            <option key={action.value} value={action.value}>
              {action.icon} {action.label}
            </option>
          ))}
        </select>
      </div>

      {config?.actionType === 'send_email' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Шаблон email
          </label>
          <select className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine">
            <option>Приветственное письмо</option>
            <option>Уведомление о заказе</option>
            <option>Напоминание</option>
          </select>
        </div>
      )}
    </div>
  );
};

const StageConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        Автоматические действия
      </label>
      <div className="text-sm text-gray-400 mb-2">
        Здесь можно настроить роботов для этой стадии
      </div>
      <button className="w-full px-3 py-2 border border-gray-600 rounded-lg text-left text-gray-300 hover:bg-gray-700/50 hover:text-gray-100 transition-colors">
        + Добавить действие
      </button>
    </div>
  );
};

const ConditionConfig: React.FC<{ config: any; onChange: (config: any) => void }> = ({
  config,
  onChange,
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        Условие
      </label>
      <input
        type="text"
        placeholder="Например: сумма > 10000"
        value={config?.condition || ''}
        onChange={(e) => onChange({ ...config, condition: e.target.value })}
        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
      />
    </div>
  );
};

const EdgeProperties: React.FC<{ edge: Edge; onUpdate: (data: any) => void }> = ({
  edge,
  onUpdate,
}) => {
  return (
    <div className="p-6">
      <h3 className="text-lg font-medium text-van-gogh-starry-night-blue mb-4">Настройки перехода</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Условие перехода
          </label>
          <input
            type="text"
            placeholder="Например: автоматически или по условию"
            value={typeof edge.label === 'string' ? edge.label : ''}
            onChange={(e) => onUpdate({ label: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Задержка (секунды)
          </label>
          <input
            type="number"
            placeholder="0"
            min="0"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-van-gogh-ultramarine"
          />
        </div>
      </div>
    </div>
  );
};
