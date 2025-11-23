import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  CpuChipIcon,
  Cog6ToothIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  WrenchScrewdriverIcon,
  ShoppingBagIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface AutomationProcess {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
  stages_count: number;
}

interface AutomationRobot {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  stage_id: number;
  actions_count: number;
}

interface AIPrompt {
  id: number;
  name: string;
  content: string;
  category: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface Service {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  is_active: boolean;
  created_at: string;
}

interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  stock_quantity: number;
  is_active: boolean;
  created_at: string;
}

export default function AIManagerSettings() {
  const [processes, setProcesses] = useState<AutomationProcess[]>([]);
  const [robots, setRobots] = useState<AutomationRobot[]>([]);
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<AIPrompt | null>(null);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  // Form states
  const [promptForm, setPromptForm] = useState({
    name: '',
    content: '',
    category: '',
    temperature: 0.7,
    max_tokens: 1000,
    model: 'gpt-4'
  });

  const [serviceForm, setServiceForm] = useState({
    name: '',
    description: '',
    price: 0,
    category: '',
    duration_hours: 1,
    unit: 'час'
  });

  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: 0,
    category: '',
    stock_quantity: 0,
    sku: '',
    unit: 'шт',
    weight_kg: 0,
    dimensions: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load data individually to handle partial failures
      try {
        const processesData = await apiService.getAutomationProcesses();
        setProcesses(processesData);
      } catch (err) {
        console.error('Failed to load processes:', err);
        setProcesses([]);
      }

      try {
        const robotsData = await apiService.getAutomationRobots();
        setRobots(robotsData);
      } catch (err) {
        console.error('Failed to load robots:', err);
        setRobots([]);
      }

      try {
        const promptsData = await apiService.getPrompts();
        setPrompts(promptsData);
      } catch (err) {
        console.error('Failed to load prompts:', err);
        setPrompts([]);
      }

      try {
        const servicesData = await apiService.getServices();
        setServices(servicesData);
      } catch (err) {
        console.error('Failed to load services:', err);
        setServices([]);
      }

      try {
        const productsData = await apiService.getProducts();
        setProducts(productsData);
      } catch (err) {
        console.error('Failed to load products:', err);
        setProducts([]);
      }
    } catch (err) {
      console.error('Failed to load AI manager data:', err);
      setError('Ошибка при загрузке данных ИИ менеджера');
    } finally {
      setLoading(false);
    }
  };

  // Prompt CRUD operations
  const handleAddPrompt = () => {
    setEditingPrompt(null);
    setPromptForm({
      name: '',
      content: '',
      category: '',
      temperature: 0.7,
      max_tokens: 1000,
      model: 'gpt-4'
    });
    setShowPromptModal(true);
  };

  const handleEditPrompt = (prompt: AIPrompt) => {
    setEditingPrompt(prompt);
    setPromptForm({
      name: prompt.name,
      content: prompt.content,
      category: prompt.category,
      temperature: 0.7,
      max_tokens: 1000,
      model: 'gpt-4'
    });
    setShowPromptModal(true);
  };

  const handleDeletePrompt = async (promptId: number) => {
    // eslint-disable-next-line no-restricted-globals
    if (confirm('Вы уверены, что хотите удалить этот промпт?')) {
      try {
        await apiService.deletePrompt(promptId);
        await loadData();
      } catch (err) {
        console.error('Failed to delete prompt:', err);
        setError('Ошибка при удалении промпта');
      }
    }
  };

  const handleSavePrompt = async () => {
    try {
      if (editingPrompt) {
        await apiService.updatePrompt(editingPrompt.id, promptForm);
      } else {
        await apiService.createPrompt(promptForm);
      }
      setShowPromptModal(false);
      await loadData();
    } catch (err) {
      console.error('Failed to save prompt:', err);
      setError('Ошибка при сохранении промпта');
    }
  };

  // Service CRUD operations
  const handleAddService = () => {
    setEditingService(null);
    setServiceForm({
      name: '',
      description: '',
      price: 0,
      category: '',
      duration_hours: 1,
      unit: 'час'
    });
    setShowServiceModal(true);
  };

  const handleEditService = (service: Service) => {
    setEditingService(service);
    setServiceForm({
      name: service.name,
      description: service.description,
      price: service.price,
      category: service.category,
      duration_hours: 1,
      unit: 'час'
    });
    setShowServiceModal(true);
  };



  const handleSaveService = async () => {
    try {
      if (editingService) {
        await apiService.updateService(editingService.id, serviceForm);
      } else {
        await apiService.createService(serviceForm);
      }
      setShowServiceModal(false);
      await loadData();
    } catch (err) {
      console.error('Failed to save service:', err);
      setError('Ошибка при сохранении услуги');
    }
  };

  // Product CRUD operations
  const handleAddProduct = () => {
    setEditingProduct(null);
    setProductForm({
      name: '',
      description: '',
      price: 0,
      category: '',
      stock_quantity: 0,
      sku: '',
      unit: 'шт',
      weight_kg: 0,
      dimensions: ''
    });
    setShowProductModal(true);
  };

  const handleEditProduct = (product: Product) => {
    setEditingProduct(product);
    setProductForm({
      name: product.name,
      description: product.description,
      price: product.price,
      category: product.category,
      stock_quantity: product.stock_quantity,
      sku: '',
      unit: 'шт',
      weight_kg: 0,
      dimensions: ''
    });
    setShowProductModal(true);
  };



  const handleSaveProduct = async () => {
    try {
      if (editingProduct) {
        await apiService.updateProduct(editingProduct.id, productForm);
      } else {
        await apiService.createProduct(productForm);
      }
      setShowProductModal(false);
      await loadData();
    } catch (err) {
      console.error('Failed to save product:', err);
      setError('Ошибка при сохранении товара');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Настройки ИИ Менеджера</h1>
          <p className="text-gray-600 mt-2">Управление процессами и роботами автоматизации</p>
        </div>
        <button
          onClick={loadData}
          className="btn-secondary flex items-center"
          disabled={loading}
        >
          <Cog6ToothIcon className="w-5 h-5 mr-2" />
          Обновить
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-red-800">{error}</div>
          </div>
        </div>
      )}

      {/* Automation Processes */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Процессы автоматизации</h3>
          <UserGroupIcon className="w-5 h-5 text-gray-600" />
        </div>

        {processes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {processes.map((process) => (
              <div key={process.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{process.name}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    process.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {process.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{process.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Тип: {process.entity_type}</span>
                  <span>Этапов: {process.stages_count}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">Процессы автоматизации не найдены</p>
        )}
      </div>

      {/* Automation Robots */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Роботы автоматизации</h3>
          <CpuChipIcon className="w-5 h-5 text-gray-600" />
        </div>

        {robots.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {robots.map((robot) => (
              <div key={robot.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{robot.name}</h4>
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-sm text-gray-600 mb-2">{robot.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Тип: {robot.entity_type}</span>
                  <span>Действий: {robot.actions_count}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">Роботы автоматизации не найдены</p>
        )}
      </div>

      {/* AI Manager Statistics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика ИИ Менеджера</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{processes.length}</div>
            <div className="text-sm text-gray-600">Процессов</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{robots.length}</div>
            <div className="text-sm text-gray-600">Роботов</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {processes.filter(p => p.is_active).length}
            </div>
            <div className="text-sm text-gray-600">Активных процессов</div>
          </div>
        </div>
      </div>

      {/* AI Prompts */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Промпты ИИ</h3>
          <DocumentTextIcon className="w-5 h-5 text-gray-600" />
        </div>

        <div className="mb-4">
          <button onClick={handleAddPrompt} className="btn-primary flex items-center">
            <PlusIcon className="w-4 h-4 mr-2" />
            Добавить промпт
          </button>
        </div>

        {prompts.length > 0 ? (
          <div className="space-y-3">
            {prompts.map((prompt) => (
              <div key={prompt.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{prompt.name}</h4>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      prompt.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {prompt.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                    <button onClick={() => handleEditPrompt(prompt)} className="p-1 text-gray-400 hover:text-gray-600">
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDeletePrompt(prompt.id)} className="p-1 text-gray-400 hover:text-red-600">
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{prompt.category}</p>
                <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                  {prompt.content && typeof prompt.content === 'string' ? (prompt.content.length > 200 ? `${prompt.content.substring(0, 200)}...` : prompt.content) : ''}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                  <span>Создан: {new Date(prompt.created_at).toLocaleDateString('ru-RU')}</span>
                  <span>Обновлен: {new Date(prompt.updated_at).toLocaleDateString('ru-RU')}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Промпты не найдены</p>
            <p className="text-sm text-gray-500 mt-1">Добавьте промпты для использования ИИ</p>
          </div>
        )}
      </div>

      {/* Services Database */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">База услуг</h3>
          <WrenchScrewdriverIcon className="w-5 h-5 text-gray-600" />
        </div>

        <div className="mb-4">
          <button onClick={handleAddService} className="btn-primary flex items-center">
            <PlusIcon className="w-4 h-4 mr-2" />
            Добавить услугу
          </button>
        </div>

        {services.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((service) => (
              <div key={service.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{service.name}</h4>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      service.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {service.is_active ? 'Активна' : 'Неактивна'}
                    </span>
                    <button onClick={() => handleEditService(service)} className="p-1 text-gray-400 hover:text-gray-600">
                      <PencilIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{service.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold text-green-600">₽{service.price}</span>
                  <span className="text-xs text-gray-500">{service.category}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <WrenchScrewdriverIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Услуги не найдены</p>
            <p className="text-sm text-gray-500 mt-1">Добавьте услуги в базу данных</p>
          </div>
        )}
      </div>

      {/* Product Catalog */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Каталог товаров</h3>
          <ShoppingBagIcon className="w-5 h-5 text-gray-600" />
        </div>

        <div className="mb-4">
          <button onClick={handleAddProduct} className="btn-primary flex items-center">
            <PlusIcon className="w-4 h-4 mr-2" />
            Добавить товар
          </button>
        </div>

        {products.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((product) => (
              <div key={product.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{product.name}</h4>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      product.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {product.is_active ? 'В наличии' : 'Отсутствует'}
                    </span>
                    <button onClick={() => handleEditProduct(product)} className="p-1 text-gray-400 hover:text-gray-600">
                      <PencilIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{product.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold text-green-600">₽{product.price}</span>
                  <span className="text-xs text-gray-500">Остаток: {product.stock_quantity} шт.</span>
                </div>
                <div className="mt-2">
                  <span className="text-xs text-gray-500">{product.category}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <ShoppingBagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Товары не найдены</p>
            <p className="text-sm text-gray-500 mt-1">Добавьте товары в каталог</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-secondary flex items-center justify-center">
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            Создать новый процесс
          </button>
          <button className="btn-secondary flex items-center justify-center">
            <CpuChipIcon className="w-5 h-5 mr-2" />
            Добавить робота
          </button>
          <button onClick={handleAddPrompt} className="btn-secondary flex items-center justify-center">
            <DocumentTextIcon className="w-5 h-5 mr-2" />
            Создать промпт
          </button>
        </div>
      </div>

      {/* Prompt Modal */}
      {showPromptModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {editingPrompt ? 'Редактировать промпт' : 'Добавить промпт'}
              </h3>
              <button onClick={() => setShowPromptModal(false)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                <input
                  type="text"
                  value={promptForm.name}
                  onChange={(e) => setPromptForm({...promptForm, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                <input
                  type="text"
                  value={promptForm.category}
                  onChange={(e) => setPromptForm({...promptForm, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Содержание</label>
                <textarea
                  value={promptForm.content}
                  onChange={(e) => setPromptForm({...promptForm, content: e.target.value})}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowPromptModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={handleSavePrompt}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {editingPrompt ? 'Сохранить' : 'Добавить'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Service Modal */}
      {showServiceModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {editingService ? 'Редактировать услугу' : 'Добавить услугу'}
              </h3>
              <button onClick={() => setShowServiceModal(false)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                <input
                  type="text"
                  value={serviceForm.name}
                  onChange={(e) => setServiceForm({...serviceForm, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                <input
                  type="text"
                  value={serviceForm.category}
                  onChange={(e) => setServiceForm({...serviceForm, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Цена (₽)</label>
                <input
                  type="number"
                  value={serviceForm.price}
                  onChange={(e) => setServiceForm({...serviceForm, price: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                <textarea
                  value={serviceForm.description}
                  onChange={(e) => setServiceForm({...serviceForm, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowServiceModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={handleSaveService}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {editingService ? 'Сохранить' : 'Добавить'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Product Modal */}
      {showProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {editingProduct ? 'Редактировать товар' : 'Добавить товар'}
              </h3>
              <button onClick={() => setShowProductModal(false)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                <input
                  type="text"
                  value={productForm.name}
                  onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                <input
                  type="text"
                  value={productForm.category}
                  onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Цена (₽)</label>
                <input
                  type="number"
                  value={productForm.price}
                  onChange={(e) => setProductForm({...productForm, price: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Количество на складе</label>
                <input
                  type="number"
                  value={productForm.stock_quantity}
                  onChange={(e) => setProductForm({...productForm, stock_quantity: parseInt(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                <textarea
                  value={productForm.description}
                  onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowProductModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={handleSaveProduct}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {editingProduct ? 'Сохранить' : 'Добавить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
