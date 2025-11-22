import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import {
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  PaperAirplaneIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  PhoneIcon,
  EnvelopeIcon,
  GlobeAltIcon,
  ChatBubbleBottomCenterTextIcon
} from '@heroicons/react/24/outline';

interface Communication {
  id: number;
  channel: string;
  direction: string;
  message_content: string;
  message_type: string;
  customer_id?: number;
  order_id?: number;
  user_id?: number;
  ai_response_id?: string;
  extra_data?: any;
  sentiment?: string;
  intent?: string;
  created_at: string;
  customer_name?: string;
  order_number?: string;
  user_name?: string;
}

interface CommunicationStats {
  total_communications: number;
  unique_customers: number;
  average_message_length: number;
  channels_breakdown: { [key: string]: number };
  sentiment_breakdown: { [key: string]: number };
}

export default function Communications() {
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [stats, setStats] = useState<CommunicationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChannel, setSelectedChannel] = useState('');
  const [selectedDirection, setSelectedDirection] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);

      // Загружаем коммуникации с фильтрами
      const params: any = {
        skip: (currentPage - 1) * 50,
        limit: 50,
        sort_by: sortBy,
        sort_order: sortOrder
      };

      if (selectedChannel) params.channel = selectedChannel;
      if (selectedDirection) params.direction = selectedDirection;
      if (selectedSentiment) params.sentiment = selectedSentiment;
      if (searchQuery) params.search = searchQuery;

      const commsResponse = await apiService.getCommunications(params);
      setCommunications(Array.isArray(commsResponse) ? commsResponse : []);

      // Загружаем статистику
      const statsResponse = await apiService.getCommunicationStats();
      setStats(statsResponse);

      // Вычисляем общее количество страниц (примерно)
      setTotalPages(Math.ceil((statsResponse?.total_communications || 0) / 50));

    } catch (error) {
      console.error('Failed to load communications:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, sortBy, sortOrder, selectedChannel, selectedDirection, selectedSentiment, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = () => {
    setCurrentPage(1);
    loadData();
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'telegram':
        return <PaperAirplaneIcon className="w-4 h-4 text-blue-600" />;
      case 'avito':
        return <ChatBubbleBottomCenterTextIcon className="w-4 h-4 text-green-600" />;
      case 'email':
        return <EnvelopeIcon className="w-4 h-4 text-purple-600" />;
      case 'phone':
        return <PhoneIcon className="w-4 h-4 text-orange-600" />;
      case 'website':
        return <GlobeAltIcon className="w-4 h-4 text-indigo-600" />;
      default:
        return <ChatBubbleLeftRightIcon className="w-4 h-4 text-gray-600" />;
    }
  };

  const getChannelLabel = (channel: string) => {
    const labels: { [key: string]: string } = {
      telegram: 'Telegram',
      avito: 'Avito',
      email: 'Email',
      phone: 'Телефон',
      website: 'Сайт'
    };
    return labels[channel] || channel;
  };

  const getDirectionLabel = (direction: string) => {
    return direction === 'inbound' ? 'Входящее' : 'Исходящее';
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-800';
      case 'neutral':
        return 'bg-gray-100 text-gray-800';
      case 'negative':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getSentimentLabel = (sentiment?: string) => {
    const labels: { [key: string]: string } = {
      positive: 'Положительное',
      neutral: 'Нейтральное',
      negative: 'Отрицательное'
    };
    return labels[sentiment || ''] || 'Не определено';
  };

  const truncateMessage = (message: string, maxLength: number = 100) => {
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
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
          <h1 className="text-2xl font-bold text-gray-900">Главная панель коммуникаций</h1>
          <p className="text-gray-600">Объединенная история всех взаимодействий с клиентами</p>
        </div>
      </div>

      {/* Статистика */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Всего коммуникаций</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_communications}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <GlobeAltIcon className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Уникальных клиентов</p>
                <p className="text-2xl font-bold text-gray-900">{stats.unique_customers}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <PaperAirplaneIcon className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Средняя длина</p>
                <p className="text-2xl font-bold text-gray-900">{Math.round(stats.average_message_length)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <FunnelIcon className="w-8 h-8 text-orange-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Каналов</p>
                <p className="text-2xl font-bold text-gray-900">{Object.keys(stats.channels_breakdown).length}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Фильтры и поиск */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="lg:col-span-2">
            <input
              type="text"
              placeholder="Поиск по сообщениям..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Все каналы</option>
            <option value="telegram">Telegram</option>
            <option value="avito">Avito</option>
            <option value="email">Email</option>
            <option value="phone">Телефон</option>
            <option value="website">Сайт</option>
          </select>

          <select
            value={selectedDirection}
            onChange={(e) => setSelectedDirection(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Все направления</option>
            <option value="inbound">Входящие</option>
            <option value="outbound">Исходящие</option>
          </select>

          <select
            value={selectedSentiment}
            onChange={(e) => setSelectedSentiment(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Все настроения</option>
            <option value="positive">Положительное</option>
            <option value="neutral">Нейтральное</option>
            <option value="negative">Отрицательное</option>
          </select>

          <button
            onClick={handleSearch}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
            Поиск
          </button>
        </div>
      </div>

      {/* Таблица коммуникаций */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('channel')}
                >
                  <div className="flex items-center">
                    Канал
                    {sortBy === 'channel' && (
                      sortOrder === 'asc' ? <ArrowUpIcon className="w-4 h-4 ml-1" /> : <ArrowDownIcon className="w-4 h-4 ml-1" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Направление
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Клиент
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Сообщение
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Настроение
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center">
                    Дата
                    {sortBy === 'date' && (
                      sortOrder === 'asc' ? <ArrowUpIcon className="w-4 h-4 ml-1" /> : <ArrowDownIcon className="w-4 h-4 ml-1" />
                    )}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {communications.map((comm) => (
                <tr key={comm.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getChannelIcon(comm.channel)}
                      <span className="ml-2 text-sm font-medium text-gray-900">
                        {getChannelLabel(comm.channel)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      comm.direction === 'inbound' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {getDirectionLabel(comm.direction)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {comm.customer_name || `ID: ${comm.customer_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={comm.message_content}>
                      {truncateMessage(comm.message_content)}
                    </div>
                    {comm.intent && (
                      <div className="text-xs text-gray-500 mt-1">
                        Намерение: {comm.intent}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSentimentColor(comm.sentiment)}`}>
                      {getSentimentLabel(comm.sentiment)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(comm.created_at).toLocaleString('ru-RU')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {communications.length === 0 && (
          <div className="text-center py-8">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Коммуникации не найдены</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery || selectedChannel || selectedDirection || selectedSentiment
                ? 'Попробуйте изменить фильтры поиска'
                : 'Пока нет коммуникаций с клиентами'
              }
            </p>
          </div>
        )}

        {/* Пагинация */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-t border-gray-200">
            <div className="text-sm text-gray-700">
              Страница {currentPage} из {totalPages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Предыдущая
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Следующая
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
