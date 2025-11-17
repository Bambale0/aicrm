import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import {
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  UserGroupIcon,
  EyeIcon,
  LinkIcon,
  XMarkIcon,
  ShoppingBagIcon
} from '@heroicons/react/24/outline';

interface AvitoChat {
  id: string;
  chat_id: string;
  customer_id?: number;
  customer_name?: string;
  message_count: number;
  last_message_at?: string;
  created_at: string;
  ai_enabled: boolean;
  item_title?: string;
  item_price?: number;
}

interface AvitoStats {
  total_chats: number;
  active_chats: number;
  messages_today: number;
  messages_month: number;
  ai_responses: number;
}

export default function Avito() {
  const navigate = useNavigate();
  const [chats, setChats] = useState<AvitoChat[]>([]);
  const [stats, setStats] = useState<AvitoStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedChat, setSelectedChat] = useState<AvitoChat | null>(null);

  useEffect(() => {
    loadAvitoData();
  }, []);

  const loadAvitoData = async () => {
    try {
      const [chatsData, statsData] = await Promise.all([
        apiService.getAvitoChats(),
        apiService.getAvitoStats()
      ]);

      setChats(chatsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load Avito data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkChat = async (chatId: string, customerId: number) => {
    try {
      // TODO: Implement Avito chat linking API
      console.log('Link Avito chat', chatId, 'to customer', customerId);
      alert('Функция будет реализована после добавления API');
    } catch (error) {
      console.error('Failed to link chat:', error);
      alert('Ошибка при связывании чата');
    }
  };

  const handleUnlinkChat = async (chatId: string) => {
    try {
      // TODO: Implement Avito chat unlinking API
      console.log('Unlink Avito chat', chatId);
      alert('Функция будет реализована после добавления API');
    } catch (error) {
      console.error('Failed to unlink chat:', error);
      alert('Ошибка при удалении связи');
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
          <h1 className="text-3xl font-bold text-gray-900">Avito</h1>
          <p className="text-gray-600 mt-2">Управление чатами Avito</p>
        </div>
      </div>

      {/* Avito Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.total_chats}</div>
            <div className="text-sm text-gray-600">Всего чатов</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">{stats.active_chats}</div>
            <div className="text-sm text-gray-600">Активных чатов</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600">{stats.messages_today}</div>
            <div className="text-sm text-gray-600">Сообщений сегодня</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-600">{stats.messages_month}</div>
            <div className="text-sm text-gray-600">Сообщений за месяц</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-indigo-600">{stats.ai_responses}</div>
            <div className="text-sm text-gray-600">AI ответов</div>
          </div>
        </div>
      )}

      {/* Avito Chats */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Чаты ({chats.length})
          </h3>
        </div>

        {chats.length > 0 ? (
          <div className="space-y-4">
            {chats.map((chat) => (
              <div key={chat.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                      <ShoppingBagIcon className="w-5 h-5 text-orange-600" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">Чат #{chat.chat_id}</h4>
                        {chat.ai_enabled && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            AI включен
                          </span>
                        )}
                      </div>

                      {chat.item_title && (
                        <p className="text-sm text-gray-600">
                          Объявление: {chat.item_title}
                          {chat.item_price && (
                            <span className="ml-2 font-medium">
                              {chat.item_price.toLocaleString('ru-RU')} ₽
                            </span>
                          )}
                        </p>
                      )}

                      {chat.customer_name && (
                        <p className="text-sm text-gray-600">
                          Клиент: {chat.customer_name}
                        </p>
                      )}

                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                        <span>{chat.message_count} сообщений</span>
                        {chat.last_message_at && (
                          <span>
                            Последнее: {new Date(chat.last_message_at).toLocaleString('ru-RU')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedChat(chat)}
                      className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>

                    {chat.customer_id ? (
                      <button
                        onClick={() => handleUnlinkChat(chat.chat_id)}
                        className="p-2 text-red-600 hover:text-red-700 rounded-lg hover:bg-red-50"
                        title="Отвязать от клиента"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleLinkChat(chat.chat_id, 1)} // TODO: Add customer selection
                        className="p-2 text-green-600 hover:text-green-700 rounded-lg hover:bg-green-50"
                        title="Связать с клиентом"
                      >
                        <LinkIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <ShoppingBagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Чаты Avito не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              Чаты появятся после настройки интеграции
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/settings/avito')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <Cog6ToothIcon className="w-5 h-5 mr-2" />
            Настройки интеграции
          </button>
          <button
            onClick={() => navigate('/customers')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <UserGroupIcon className="w-5 h-5 mr-2" />
            Управление клиентами
          </button>
          <button
            onClick={() => navigate('/communications')}
            className="btn-secondary flex items-center justify-center py-3"
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2" />
            История коммуникаций
          </button>
        </div>
      </div>

      {/* Chat Details Modal */}
      {selectedChat && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Чат Avito #{selectedChat.chat_id}
              </h3>
              <button
                onClick={() => setSelectedChat(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">ID чата</label>
                  <p className="text-gray-900">{selectedChat.chat_id}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">AI ответы</label>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    selectedChat.ai_enabled
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedChat.ai_enabled ? 'Включены' : 'Отключены'}
                  </span>
                </div>
              </div>

              {selectedChat.item_title && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Объявление</label>
                  <p className="text-gray-900">{selectedChat.item_title}</p>
                  {selectedChat.item_price && (
                    <p className="text-sm text-gray-600 mt-1">
                      Цена: {selectedChat.item_price.toLocaleString('ru-RU')} ₽
                    </p>
                  )}
                </div>
              )}

              {selectedChat.customer_name && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Связанный клиент</label>
                  <p className="text-gray-900">{selectedChat.customer_name}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Сообщений</label>
                  <p className="text-gray-900">{selectedChat.message_count}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Последнее сообщение</label>
                  <p className="text-gray-900">
                    {selectedChat.last_message_at
                      ? new Date(selectedChat.last_message_at).toLocaleString('ru-RU')
                      : 'Нет'
                    }
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Создан</label>
                <p className="text-xs text-gray-600">
                  {new Date(selectedChat.created_at).toLocaleString('ru-RU')}
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => setSelectedChat(null)}
                className="btn-secondary"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
