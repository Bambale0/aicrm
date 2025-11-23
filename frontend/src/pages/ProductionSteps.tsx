import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface ProductionStep {
  id: number;
  name: string;
  description: string;
  sequence_number: number;
  status: string;
  estimated_hours: number | null;
  actual_hours: number | null;
  started_at: string | null;
  completed_at: string | null;
  is_overdue: boolean;
  progress_percentage: number;
}

interface ProductionProgress {
  total_steps: number;
  completed_steps: number;
  in_progress_steps: number;
  pending_steps: number;
  progress: number;
  current_step: string | null;
  next_step: string | null;
  is_overdue: boolean;
  steps: ProductionStep[];
}

interface Order {
  id: number;
  customer_name: string;
  status: string;
  created_at: string;
}

const ProductionSteps: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [progress, setProgress] = useState<ProductionProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [selectedStep, setSelectedStep] = useState<ProductionStep | null>(null);
  const [completeData, setCompleteData] = useState({
    actual_hours: '',
    notes: ''
  });

  // Load orders on component mount
  useEffect(() => {
    loadOrders();
  }, []);

  // Load progress when order is selected
  useEffect(() => {
    if (selectedOrder) {
      loadProductionProgress(selectedOrder.id);
    }
  }, [selectedOrder]);

  const loadOrders = async () => {
    try {
      const ordersData = await apiService.getOrders();
      // Ensure ordersData is an array and transform data to match expected interface
      const transformedOrders = Array.isArray(ordersData) ? ordersData.map(order => ({
        id: order.id,
        customer_name: order.customer_name || 'Неизвестный клиент',
        status: order.status || 'unknown',
        created_at: order.created_at || new Date().toISOString()
      })) : [];
      setOrders(transformedOrders);
    } catch (error) {
      console.error('Error loading orders:', error);
      setOrders([]);
    }
  };

  const loadProductionProgress = async (orderId: number) => {
    setLoading(true);
    try {
      const data = await apiService.getOrderProductionProgress(orderId);
      setProgress(data);
    } catch (error) {
      console.error('Error loading production progress:', error);
      setProgress(null);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStep = async (orderId: number, stepId: number) => {
    try {
      await apiService.startProductionStep(orderId, stepId);
      loadProductionProgress(orderId);
      alert('Этап запущен успешно');
    } catch (error) {
      console.error('Error starting step:', error);
      alert('Ошибка при запуске этапа');
    }
  };

  const handleCompleteStep = async () => {
    if (!selectedStep || !selectedOrder) return;

    try {
      await apiService.completeProductionStep(selectedOrder.id, selectedStep.id, {
        actual_hours: completeData.actual_hours ? parseFloat(completeData.actual_hours) : undefined,
        notes: completeData.notes || undefined
      });
      setShowCompleteModal(false);
      setSelectedStep(null);
      setCompleteData({ actual_hours: '', notes: '' });
      loadProductionProgress(selectedOrder.id);
      alert('Этап завершен успешно');
    } catch (error) {
      console.error('Error completing step:', error);
      alert('Ошибка при завершении этапа');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      case 'blocked': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Завершен';
      case 'in_progress': return 'В работе';
      case 'pending': return 'Ожидает';
      case 'blocked': return 'Заблокирован';
      case 'cancelled': return 'Отменен';
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Управление этапами производства</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Orders List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow border">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Заказы в производстве</h3>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {orders.map((order) => (
                <div
                  key={order.id}
                  className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedOrder?.id === order.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedOrder(order)}
                >
                  <div className="font-medium">Заказ #{order.id}</div>
                  <div className="text-sm text-gray-600">{order.customer_name}</div>
                  <div className="text-xs text-gray-500">
                    {formatDate(order.created_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Production Progress */}
        <div className="lg:col-span-3">
          {selectedOrder ? (
            <div className="space-y-6">
              {/* Order Info */}
              <div className="bg-white rounded-lg shadow border p-4">
                <h2 className="text-xl font-bold mb-2">
                  Заказ #{selectedOrder.id} - {selectedOrder.customer_name}
                </h2>
                <div className="text-sm text-gray-600">
                  Статус: {selectedOrder.status} | Создан: {formatDate(selectedOrder.created_at)}
                </div>
              </div>

              {/* Progress Overview */}
              {progress && (
                <div className="bg-white rounded-lg shadow border p-4">
                  <h3 className="text-lg font-semibold mb-4">Прогресс производства</h3>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Общий прогресс</span>
                      <span>{progress.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress.progress}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{progress.total_steps}</div>
                      <div className="text-sm text-gray-600">Всего этапов</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{progress.completed_steps}</div>
                      <div className="text-sm text-gray-600">Завершено</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{progress.in_progress_steps}</div>
                      <div className="text-sm text-gray-600">В работе</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-600">{progress.pending_steps}</div>
                      <div className="text-sm text-gray-600">Ожидает</div>
                    </div>
                  </div>

                  {/* Current Status */}
                  <div className="space-y-2">
                    {progress.current_step && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Текущий этап:</span>
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                          {progress.current_step}
                        </span>
                      </div>
                    )}
                    {progress.next_step && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Следующий этап:</span>
                        <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm">
                          {progress.next_step}
                        </span>
                      </div>
                    )}
                    {progress.is_overdue && (
                      <div className="flex items-center gap-2">
                        <span className="text-red-500">⚠️</span>
                        <span className="text-sm text-red-600 font-medium">Есть просроченные этапы</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Steps List */}
              {progress && (
                <div className="bg-white rounded-lg shadow border">
                  <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold">Этапы производства</h3>
                  </div>
                  <div className="p-4">
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <div className="animate-spin">⏳</div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {progress.steps.map((step) => (
                          <div key={step.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-medium">
                                  #{step.sequence_number}
                                </span>
                                <h4 className="font-medium">{step.name}</h4>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(step.status)}`}>
                                  {getStatusText(step.status)}
                                </span>
                                {step.is_overdue && (
                                  <span className="text-red-500 text-sm">⚠️ Просрочен</span>
                                )}
                              </div>

                              {step.status === 'pending' && (
                                <button
                                  onClick={() => handleStartStep(selectedOrder.id, step.id)}
                                  className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                                >
                                  Начать
                                </button>
                              )}

                              {step.status === 'in_progress' && (
                                <button
                                  onClick={() => {
                                    setSelectedStep(step);
                                    setShowCompleteModal(true);
                                  }}
                                  className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                                >
                                  Завершить
                                </button>
                              )}
                            </div>

                            {step.description && (
                              <p className="text-sm text-gray-600 mb-3">{step.description}</p>
                            )}

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              {step.estimated_hours && (
                                <div>
                                  <span className="font-medium">План:</span> {step.estimated_hours} ч
                                </div>
                              )}
                              {step.actual_hours && (
                                <div>
                                  <span className="font-medium">Факт:</span> {step.actual_hours} ч
                                </div>
                              )}
                              {step.started_at && (
                                <div>
                                  <span className="font-medium">Начало:</span> {formatDate(step.started_at)}
                                </div>
                              )}
                              {step.completed_at && (
                                <div>
                                  <span className="font-medium">Завершение:</span> {formatDate(step.completed_at)}
                                </div>
                              )}
                            </div>

                            {/* Progress bar for individual step */}
                            <div className="mt-3">
                              <div className="flex justify-between text-xs mb-1">
                                <span>Прогресс этапа</span>
                                <span>{step.progress_percentage}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1">
                                <div
                                  className="bg-green-600 h-1 rounded-full transition-all duration-300"
                                  style={{ width: `${step.progress_percentage}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow border p-8 text-center">
              <div className="text-gray-500 text-lg">Выберите заказ для просмотра этапов производства</div>
            </div>
          )}
        </div>
      </div>

      {/* Complete Step Modal */}
      {showCompleteModal && selectedStep && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Завершить этап</h2>
              <button
                onClick={() => setShowCompleteModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="font-medium">{selectedStep.name}</h3>
                <p className="text-sm text-gray-600">{selectedStep.description}</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Фактическое время (часы):</label>
                <input
                  type="number"
                  step="0.5"
                  value={completeData.actual_hours}
                  onChange={(e) => setCompleteData({ ...completeData, actual_hours: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="2.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Комментарии:</label>
                <textarea
                  value={completeData.notes}
                  onChange={(e) => setCompleteData({ ...completeData, notes: e.target.value })}
                  className="w-full px-3 py-2 border rounded h-24"
                  placeholder="Комментарии к выполненной работе..."
                />
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowCompleteModal(false)}
                  className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  onClick={handleCompleteStep}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Завершить
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductionSteps;
