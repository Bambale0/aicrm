"""
Основной сервис автоматизации в стиле Bitrix24
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ...models.automation import EntityType, TriggerEvent
from .robot_service import RobotService
from .trigger_service import TriggerService

logger = logging.getLogger(__name__)


class AutomationService:
    """
    Главный сервис автоматизации, объединяющий триггеры и роботов
    """

    def __init__(self, db: Session):
        self.db = db
        self.trigger_service = TriggerService(db)
        self.robot_service = RobotService(db)

    async def handle_event(
        self,
        entity_type: EntityType,
        event_type: TriggerEvent,
        entity_id: int,
        event_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Обработка события - сначала триггеры, потом роботы
        """
        logger.info(
            f"Processing automation event: {entity_type.value}.{event_type.value} for entity {entity_id}"
        )

        results = {
            "entity_type": entity_type.value,
            "event_type": event_type.value,
            "entity_id": entity_id,
            "triggers_executed": [],
            "robots_executed": [],
            "overall_success": True,
        }

        try:
            # 1. Выполняем триггеры
            trigger_results = await self.trigger_service.handle_trigger_event(
                entity_type, event_type, entity_id, event_data
            )
            results["triggers_executed"] = trigger_results

            # 2. Если триггеры переместили сущность на новую стадию,
            # роботы новой стадии выполнятся автоматически в trigger_service

            results["overall_success"] = all(
                result.get("success", False) for result in trigger_results
            )

        except Exception as e:
            logger.error(f"Error processing automation event: {e}")
            results["overall_success"] = False
            results["error"] = str(e)

        return results

    async def move_to_stage(
        self, entity_type: EntityType, entity_id: int, stage_id: int
    ) -> Dict[str, Any]:
        """
        Ручное перемещение сущности на стадию с выполнением роботов
        """
        logger.info(
            f"Manually moving {entity_type.value} {entity_id} to stage {stage_id}"
        )

        try:
            # Перемещаем через триггер сервис (он включает выполнение роботов)
            move_result = await self.trigger_service._move_to_target_stage(
                entity_type, entity_id, stage_id
            )

            # Выполняем роботов новой стадии
            robot_results = await self.robot_service.execute_stage_robots(
                entity_type, entity_id, stage_id
            )

            return {
                "success": True,
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "stage_id": stage_id,
                "move_result": move_result,
                "robots_executed": robot_results,
            }

        except Exception as e:
            logger.error(f"Error moving to stage: {e}")
            return {
                "success": False,
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "stage_id": stage_id,
                "error": str(e),
            }

    # Специфические методы для разных типов событий

    async def on_customer_created(self, customer_id: int) -> Dict[str, Any]:
        """Клиент создан"""
        return await self.handle_event(
            EntityType.CUSTOMER, TriggerEvent.CUSTOMER_CREATED, customer_id
        )

    async def on_customer_updated(
        self, customer_id: int, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Клиент обновлен"""
        return await self.handle_event(
            EntityType.CUSTOMER,
            TriggerEvent.CUSTOMER_UPDATED,
            customer_id,
            {"changes": changes},
        )

    async def on_customer_loyalty_changed(
        self, customer_id: int, old_level: str, new_level: str
    ) -> Dict[str, Any]:
        """Изменен уровень лояльности клиента"""
        return await self.handle_event(
            EntityType.CUSTOMER,
            TriggerEvent.CUSTOMER_LOYALTY_CHANGED,
            customer_id,
            {"old_level": old_level, "new_level": new_level},
        )

    async def on_order_created(self, order_id: int) -> Dict[str, Any]:
        """Заказ создан"""
        return await self.handle_event(
            EntityType.ORDER, TriggerEvent.ORDER_CREATED, order_id
        )

    async def on_order_status_changed(
        self, order_id: int, old_status: str, new_status: str
    ) -> Dict[str, Any]:
        """Статус заказа изменен"""
        return await self.handle_event(
            EntityType.ORDER,
            TriggerEvent.ORDER_STATUS_CHANGED,
            order_id,
            {"old_status": old_status, "new_status": new_status},
        )

    async def on_order_completed(self, order_id: int) -> Dict[str, Any]:
        """Заказ завершен"""
        return await self.handle_event(
            EntityType.ORDER, TriggerEvent.ORDER_COMPLETED, order_id
        )

    async def on_payment_received(self, order_id: int, amount: float) -> Dict[str, Any]:
        """Получена оплата"""
        return await self.handle_event(
            EntityType.ORDER,
            TriggerEvent.PAYMENT_RECEIVED,
            order_id,
            {"amount": amount},
        )

    async def on_task_created(self, task_id: int) -> Dict[str, Any]:
        """Задача создана"""
        return await self.handle_event(
            EntityType.TASK, TriggerEvent.TASK_CREATED, task_id
        )

    async def on_task_status_changed(
        self, task_id: int, old_status: str, new_status: str
    ) -> Dict[str, Any]:
        """Статус задачи изменен"""
        return await self.handle_event(
            EntityType.TASK,
            TriggerEvent.TASK_STATUS_CHANGED,
            task_id,
            {"old_status": old_status, "new_status": new_status},
        )

    async def on_task_completed(self, task_id: int) -> Dict[str, Any]:
        """Задача завершена"""
        return await self.handle_event(
            EntityType.TASK, TriggerEvent.TASK_COMPLETED, task_id
        )

    async def on_deadline_approaching(
        self, task_id: int, hours_left: int
    ) -> Dict[str, Any]:
        """Приближается дедлайн задачи"""
        return await self.handle_event(
            EntityType.TASK,
            TriggerEvent.DEADLINE_APPROACHING,
            task_id,
            {"hours_left": hours_left},
        )

    async def on_production_started(self, order_id: int) -> Dict[str, Any]:
        """Производство начато"""
        return await self.handle_event(
            EntityType.ORDER, TriggerEvent.PRODUCTION_STARTED, order_id
        )

    async def on_production_step_completed(self, step_id: int) -> Dict[str, Any]:
        """Этап производства завершен"""
        return await self.handle_event(
            EntityType.PRODUCTION_STEP, TriggerEvent.PRODUCTION_STEP_COMPLETED, step_id
        )

    async def on_production_completed(self, order_id: int) -> Dict[str, Any]:
        """Производство завершено"""
        return await self.handle_event(
            EntityType.ORDER, TriggerEvent.PRODUCTION_COMPLETED, order_id
        )

    async def on_production_overdue(
        self, step_id: int, overdue_hours: float
    ) -> Dict[str, Any]:
        """Производство просрочено"""
        return await self.handle_event(
            EntityType.PRODUCTION_STEP,
            TriggerEvent.PRODUCTION_OVERDUE,
            step_id,
            {"overdue_hours": overdue_hours},
        )

    async def on_message_received(
        self, communication_id: int, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Получено сообщение"""
        return await self.handle_event(
            entity_type,
            TriggerEvent.MESSAGE_RECEIVED,
            entity_id,
            {"communication_id": communication_id},
        )

    async def on_message_sent(
        self, communication_id: int, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Отправлено сообщение"""
        return await self.handle_event(
            entity_type,
            TriggerEvent.MESSAGE_SENT,
            entity_id,
            {"communication_id": communication_id},
        )

    async def on_email_opened(
        self, communication_id: int, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Email открыт"""
        return await self.handle_event(
            entity_type,
            TriggerEvent.EMAIL_OPENED,
            entity_id,
            {"communication_id": communication_id},
        )

    # ИИ-функционал для генерации и оптимизации цепочек автоматизации

    async def generate_automation_chain_with_ai(
        self,
        description: str,
        entity_type: EntityType,
        complexity_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        ИИ-генерация цепочки автоматизации на основе описания бизнес-процесса

        Args:
            description: Описание процесса на естественном языке
            entity_type: Тип сущности
            complexity_level: Уровень сложности (simple, medium, complex)

        Returns:
            Dict с результатом генерации
        """
        try:
            # Импортируем AI клиент для генерации
            from ...services.ai.client import AIClient

            ai_client = AIClient()

            # Создаем промпт для ИИ
            prompt = self._build_generation_prompt(
                description, entity_type, complexity_level
            )

            # Генерируем цепочку через ИИ
            ai_response = await ai_client.generate_automation_chain(prompt)

            if not ai_response.get("success"):
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI generation failed"),
                }

            # Парсим и применяем сгенерированную цепочку
            generated_data = ai_response.get("generated_chain", {})
            applied_changes = await self._apply_generated_chain(
                generated_data, entity_type
            )

            return {
                "success": True,
                "message": "Automation chain generated and applied successfully",
                "generated_process": generated_data,
                "applied_changes": applied_changes,
            }

        except Exception as e:
            logger.error(f"Error generating automation chain with AI: {e}")
            return {"success": False, "error": f"AI generation failed: {str(e)}"}

    async def optimize_automation_chain_with_ai(
        self, process_id: int, optimization_goal: str
    ) -> Dict[str, Any]:
        """
        ИИ-оптимизация существующей цепочки автоматизации

        Args:
            process_id: ID процесса для оптимизации
            optimization_goal: Цель оптимизации (performance, reliability, cost)

        Returns:
            Dict с результатом оптимизации
        """
        try:
            # Получаем текущий процесс
            process = self.db.query(Process).filter(Process.id == process_id).first()
            if not process:
                return {"success": False, "error": "Process not found"}

            # Собираем данные о текущей автоматизации
            current_data = await self._collect_process_data(process_id)

            # Импортируем AI клиент
            from ...services.ai.client import AIClient

            ai_client = AIClient()

            # Создаем промпт для оптимизации
            prompt = self._build_optimization_prompt(current_data, optimization_goal)

            # Получаем оптимизации от ИИ
            ai_response = await ai_client.optimize_automation_chain(prompt)

            if not ai_response.get("success"):
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI optimization failed"),
                }

            # Применяем оптимизации
            optimizations = ai_response.get("optimizations", [])
            applied_optimizations = await self._apply_optimizations(
                process_id, optimizations
            )

            return {
                "success": True,
                "message": f"Automation chain optimized for {optimization_goal}",
                "optimizations_applied": applied_optimizations,
                "performance_improvements": ai_response.get("performance_improvements"),
            }

        except Exception as e:
            logger.error(f"Error optimizing automation chain with AI: {e}")
            return {"success": False, "error": f"AI optimization failed: {str(e)}"}

    async def analyze_and_suggest_improvements(
        self, entity_type: EntityType = None, analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        ИИ-анализ автоматизации и предложения по улучшению

        Args:
            entity_type: Тип сущности для анализа (опционально)
            analysis_period_days: Период анализа в днях

        Returns:
            Dict с анализом и предложениями
        """
        try:
            # Собираем статистику за период
            stats = await self._collect_automation_stats(
                entity_type, analysis_period_days
            )

            # Импортируем AI клиент
            from ...services.ai.client import AIClient

            ai_client = AIClient()

            # Создаем промпт для анализа
            prompt = self._build_analysis_prompt(stats, entity_type)

            # Получаем анализ и предложения от ИИ
            ai_response = await ai_client.analyze_automation(prompt)

            if not ai_response.get("success"):
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI analysis failed"),
                }

            return {
                "analysis_period": {
                    "days": analysis_period_days,
                    "entity_type": entity_type.value if entity_type else "all",
                },
                "total_processes": stats.get("total_processes", 0),
                "active_triggers": stats.get("active_triggers", 0),
                "executed_robots": stats.get("executed_robots", 0),
                "success_rate": stats.get("success_rate", 0.0),
                "bottlenecks": ai_response.get("bottlenecks", []),
                "suggestions": ai_response.get("suggestions", []),
                "performance_metrics": stats.get("performance_metrics", {}),
            }

        except Exception as e:
            logger.error(f"Error analyzing automation with AI: {e}")
            return {"success": False, "error": f"AI analysis failed: {str(e)}"}

    # Вспомогательные методы для работы с ИИ

    def _build_generation_prompt(
        self, description: str, entity_type: EntityType, complexity_level: str
    ) -> str:
        """Создает промпт для генерации цепочки автоматизации"""
        return f"""
Ты - эксперт по бизнес-автоматизации. Проанализируй описание бизнес-процесса и создай полную цепочку автоматизации.

Описание процесса: {description}
Тип сущности: {entity_type.value}
Уровень сложности: {complexity_level}

Требуется создать:
1. Стадии процесса (stages) - последовательные этапы жизненного цикла
2. Триггеры (triggers) - условия автоматического перехода между стадиями
3. Роботы (robots) - автоматические действия на каждой стадии

Для каждой стадии укажи:
- name: название стадии
- description: описание
- order_index: порядок выполнения
- color: HEX цвет для визуализации

Для каждого триггера укажи:
- name: название триггера
- description: описание
- event_type: тип события (из доступных: customer_created, order_completed, etc.)
- conditions: условия срабатывания (опционально)
- target_stage_id: ID целевой стадии

Для каждого робота укажи:
- name: название робота
- description: описание
- stage_id: ID стадии
- actions: список действий (action_type, config, conditions, delay_seconds)

Ответь в формате JSON с ключами: stages, triggers, robots.
"""

    def _build_optimization_prompt(
        self, current_data: Dict[str, Any], optimization_goal: str
    ) -> str:
        """Создает промпт для оптимизации цепочки"""
        return f"""
Ты - эксперт по оптимизации бизнес-процессов. Проанализируй текущую цепочку автоматизации и предложи оптимизации.

Текущие данные: {current_data}
Цель оптимизации: {optimization_goal}

Доступные цели оптимизации:
- performance: улучшение скорости выполнения
- reliability: повышение надежности
- cost: снижение затрат на выполнение

Предложи конкретные изменения:
1. Удаление ненужных шагов
2. Объединение действий
3. Изменение условий срабатывания
4. Добавление новых триггеров/роботов
5. Изменение порядка выполнения

Ответь в формате JSON с ключами: optimizations, performance_improvements.
"""

    def _build_analysis_prompt(
        self, stats: Dict[str, Any], entity_type: EntityType = None
    ) -> str:
        """Создает промпт для анализа автоматизации"""
        return f"""
Ты - эксперт по анализу бизнес-автоматизации. Проанализируй статистику и предложи улучшения.

Статистика: {stats}
Тип сущности: {entity_type.value if entity_type else 'все'}

Найди:
1. Узкие места (bottlenecks) - медленные или часто падающие процессы
2. Возможности оптимизации - неэффективные цепочки
3. Новые сценарии автоматизации - упущенные возможности

Для каждого предложения укажи:
- type: bottleneck/optimization/new_scenario
- title: краткий заголовок
- description: подробное описание
- impact_level: low/medium/high
- implementation_complexity: low/medium/high
- estimated_benefit: ожидаемая польза
- suggested_actions: конкретные действия

Ответь в формате JSON с ключами: bottlenecks, suggestions.
"""

    async def _apply_generated_chain(
        self, generated_data: Dict[str, Any], entity_type: EntityType
    ) -> Dict[str, Any]:
        """Применяет сгенерированную цепочку автоматизации"""
        applied_changes = {
            "processes_created": 0,
            "stages_created": 0,
            "triggers_created": 0,
            "robots_created": 0,
        }

        try:
            # Создаем процесс
            from ...models.automation import Process

            process = Process(
                name=generated_data.get(
                    "name", f"Generated {entity_type.value} Process"
                ),
                description=generated_data.get("description", "AI-generated process"),
                entity_type=entity_type,
                is_active=True,
            )
            self.db.add(process)
            self.db.flush()
            applied_changes["processes_created"] = 1

            # Создаем стадии
            stages_data = generated_data.get("stages", [])
            stage_id_map = {}

            for i, stage_data in enumerate(stages_data):
                from ...models.automation import Stage

                stage = Stage(
                    name=stage_data["name"],
                    description=stage_data.get("description", ""),
                    entity_type=entity_type,
                    process_id=process.id,
                    order_index=stage_data.get("order_index", i),
                    color=stage_data.get("color", "#FFFFFF"),
                    is_active=True,
                )
                self.db.add(stage)
                self.db.flush()
                stage_id_map[i] = stage.id
                applied_changes["stages_created"] += 1

            # Создаем триггеры
            triggers_data = generated_data.get("triggers", [])
            for trigger_data in triggers_data:
                from ...models.automation import Trigger

                target_stage_index = trigger_data.get("target_stage_index", 0)
                target_stage_id = stage_id_map.get(target_stage_index)

                if target_stage_id:
                    trigger = Trigger(
                        name=trigger_data["name"],
                        description=trigger_data.get("description", ""),
                        entity_type=entity_type,
                        event_type=trigger_data["event_type"],
                        conditions=trigger_data.get("conditions"),
                        target_stage_id=target_stage_id,
                        is_active=True,
                    )
                    self.db.add(trigger)
                    applied_changes["triggers_created"] += 1

            # Создаем роботов
            robots_data = generated_data.get("robots", [])
            for robot_data in robots_data:
                from ...models.automation import Robot

                stage_index = robot_data.get("stage_index", 0)
                stage_id = stage_id_map.get(stage_index)

                if stage_id:
                    robot = Robot(
                        name=robot_data["name"],
                        description=robot_data.get("description", ""),
                        entity_type=entity_type,
                        stage_id=stage_id,
                        is_active=True,
                    )
                    self.db.add(robot)
                    self.db.flush()

                    # Создаем действия робота
                    actions_data = robot_data.get("actions", [])
                    for action_data in actions_data:
                        from ...models.automation import RobotActionConfig

                        action_config = RobotActionConfig(
                            robot_id=robot.id,
                            action_type=action_data["action_type"],
                            execution_order=action_data.get("execution_order", 1),
                            config=action_data.get("config", {}),
                            conditions=action_data.get("conditions"),
                            delay_seconds=action_data.get("delay_seconds", 0),
                        )
                        self.db.add(action_config)

                    applied_changes["robots_created"] += 1

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error applying generated chain: {e}")
            applied_changes["error"] = str(e)

        return applied_changes

    async def _apply_optimizations(
        self, process_id: int, optimizations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Применяет оптимизации к процессу"""
        applied = []

        for optimization in optimizations:
            try:
                opt_type = optimization.get("type")
                if opt_type == "remove_step":
                    # Удаление шага
                    step_id = optimization.get("step_id")
                    # Логика удаления
                    applied.append({"type": "removed", "step_id": step_id})
                elif opt_type == "add_trigger":
                    # Добавление триггера
                    trigger_data = optimization.get("trigger_data")
                    # Логика создания триггера
                    applied.append({"type": "trigger_added", "trigger": trigger_data})
                # Другие типы оптимизаций...

            except Exception as e:
                logger.error(f"Error applying optimization {optimization}: {e}")

        return applied

    async def _collect_process_data(self, process_id: int) -> Dict[str, Any]:
        """Собирает данные о процессе для анализа"""
        # Логика сбора данных о процессе
        return {"process_id": process_id, "stages": [], "triggers": [], "robots": []}

    async def _collect_automation_stats(
        self, entity_type: EntityType = None, days: int = 30
    ) -> Dict[str, Any]:
        """Собирает статистику автоматизации"""
        # Логика сбора статистики
        return {
            "total_processes": 0,
            "active_triggers": 0,
            "executed_robots": 0,
            "success_rate": 0.0,
            "performance_metrics": {},
        }
