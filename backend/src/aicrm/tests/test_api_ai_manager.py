"""
Интеграционные тесты для AI Manager API
"""
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestAIManagerApi:
    """Тесты для AI Manager API"""

    # AI Prompts endpoints

    async def test_get_prompts_success(self, async_client: AsyncClient):
        """Тест успешного получения всех промптов"""
        response = await async_client.get("/ai-manager/prompts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_active_prompts_success(self, async_client: AsyncClient):
        """Тест успешного получения активных промптов"""
        response = await async_client.get("/ai-manager/prompts/active")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_prompt_by_id_success(self, async_client: AsyncClient):
        """Тест успешного получения промпта по ID"""
        # Сначала создаем промпт
        create_data = {
            "name": "Test Prompt",
            "content": "Test content",
            "description": "Test description",
            "is_active": True
        }

        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_prompt = MagicMock()
            mock_prompt.id = 1
            mock_prompt.name = "Test Prompt"
            mock_prompt.content = "Test content"
            mock_prompt.description = "Test description"
            mock_prompt.is_active = True
            mock_service.create_prompt.return_value = mock_prompt
            mock_service.get_prompt_by_id.return_value = mock_prompt
            mock_service_class.return_value = mock_service

            # Создаем промпт
            create_response = await async_client.post("/ai-manager/prompts", json=create_data)
            assert create_response.status_code == 201

            # Получаем промпт по ID
            response = await async_client.get("/ai-manager/prompts/1")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Prompt"
            assert data["content"] == "Test content"

    async def test_get_prompt_by_id_not_found(self, async_client: AsyncClient):
        """Тест получения несуществующего промпта"""
        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_prompt_by_id.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/prompts/999")

            assert response.status_code == 404
            assert "Промпт не найден" in response.json()["detail"]

    async def test_create_prompt_success(self, async_client: AsyncClient):
        """Тест успешного создания промпта"""
        create_data = {
            "name": "New Test Prompt",
            "content": "New test content",
            "description": "New test description",
            "is_active": True
        }

        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_prompt = MagicMock()
            mock_prompt.id = 1
            mock_prompt.name = "New Test Prompt"
            mock_prompt.content = "New test content"
            mock_prompt.description = "New test description"
            mock_prompt.is_active = True
            mock_service.create_prompt.return_value = mock_prompt
            mock_service_class.return_value = mock_service

            response = await async_client.post("/ai-manager/prompts", json=create_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Test Prompt"
            assert data["content"] == "New test content"

    async def test_update_prompt_success(self, async_client: AsyncClient):
        """Тест успешного обновления промпта"""
        update_data = {
            "name": "Updated Prompt",
            "content": "Updated content"
        }

        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_prompt = MagicMock()
            mock_prompt.id = 1
            mock_prompt.name = "Updated Prompt"
            mock_prompt.content = "Updated content"
            mock_service.update_prompt.return_value = mock_prompt
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/prompts/1", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Prompt"

    async def test_update_prompt_not_found(self, async_client: AsyncClient):
        """Тест обновления несуществующего промпта"""
        update_data = {"name": "Updated Prompt"}

        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_prompt.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/prompts/999", json=update_data)

            assert response.status_code == 404
            assert "Промпт не найден" in response.json()["detail"]

    async def test_delete_prompt_success(self, async_client: AsyncClient):
        """Тест успешного удаления промпта"""
        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_prompt.return_value = True
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/prompts/1")

            assert response.status_code == 204

    async def test_delete_prompt_not_found(self, async_client: AsyncClient):
        """Тест удаления несуществующего промпта"""
        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_prompt.return_value = False
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/prompts/999")

            assert response.status_code == 404
            assert "Промпт не найден" in response.json()["detail"]

    async def test_toggle_prompt_status_success(self, async_client: AsyncClient):
        """Тест успешного переключения статуса промпта"""
        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_prompt = MagicMock()
            mock_prompt.id = 1
            mock_prompt.is_active = False
            mock_service.toggle_prompt_status.return_value = mock_prompt
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/prompts/1/toggle")

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False

    async def test_toggle_prompt_status_not_found(self, async_client: AsyncClient):
        """Тест переключения статуса несуществующего промпта"""
        with patch("src.aicrm.services.ai_prompt_service.AIPromptService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.toggle_prompt_status.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/prompts/999/toggle")

            assert response.status_code == 404
            assert "Промпт не найден" in response.json()["detail"]

    # Services endpoints

    async def test_get_services_success(self, async_client: AsyncClient):
        """Тест успешного получения всех услуг"""
        response = await async_client.get("/ai-manager/services")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_active_services_success(self, async_client: AsyncClient):
        """Тест успешного получения активных услуг"""
        response = await async_client.get("/ai-manager/services/active")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_service_by_id_success(self, async_client: AsyncClient):
        """Тест успешного получения услуги по ID"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_svc = MagicMock()
            mock_svc.id = 1
            mock_svc.name = "Test Service"
            mock_service.get_service_by_id.return_value = mock_svc
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/services/1")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Service"

    async def test_get_service_by_id_not_found(self, async_client: AsyncClient):
        """Тест получения несуществующей услуги"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_service_by_id.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/services/999")

            assert response.status_code == 404
            assert "Услуга не найдена" in response.json()["detail"]

    async def test_create_service_success(self, async_client: AsyncClient):
        """Тест успешного создания услуги"""
        create_data = {
            "name": "New Test Service",
            "description": "New test description",
            "price": 1000.00,
            "category": "test",
            "is_active": True
        }

        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_svc = MagicMock()
            mock_svc.id = 1
            mock_svc.name = "New Test Service"
            mock_svc.description = "New test description"
            mock_svc.price = 1000.00
            mock_svc.category = "test"
            mock_svc.is_active = True
            mock_service.create_service.return_value = mock_svc
            mock_service_class.return_value = mock_service

            response = await async_client.post("/ai-manager/services", json=create_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Test Service"

    async def test_update_service_success(self, async_client: AsyncClient):
        """Тест успешного обновления услуги"""
        update_data = {
            "name": "Updated Service",
            "price": 1500.00
        }

        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_svc = MagicMock()
            mock_svc.id = 1
            mock_svc.name = "Updated Service"
            mock_svc.price = 1500.00
            mock_service.update_service.return_value = mock_svc
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/services/1", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Service"

    async def test_update_service_not_found(self, async_client: AsyncClient):
        """Тест обновления несуществующей услуги"""
        update_data = {"name": "Updated Service"}

        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_service.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/services/999", json=update_data)

            assert response.status_code == 404
            assert "Услуга не найдена" in response.json()["detail"]

    async def test_delete_service_success(self, async_client: AsyncClient):
        """Тест успешного удаления услуги"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_service.return_value = True
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/services/1")

            assert response.status_code == 204

    async def test_delete_service_not_found(self, async_client: AsyncClient):
        """Тест удаления несуществующей услуги"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_service.return_value = False
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/services/999")

            assert response.status_code == 404
            assert "Услуга не найдена" in response.json()["detail"]

    async def test_toggle_service_status_success(self, async_client: AsyncClient):
        """Тест успешного переключения статуса услуги"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_svc = MagicMock()
            mock_svc.id = 1
            mock_svc.is_active = False
            mock_service.toggle_service_status.return_value = mock_svc
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/services/1/toggle")

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False

    async def test_toggle_service_status_not_found(self, async_client: AsyncClient):
        """Тест переключения статуса несуществующей услуги"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.toggle_service_status.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/services/999/toggle")

            assert response.status_code == 404
            assert "Услуга не найдена" in response.json()["detail"]

    async def test_get_service_categories_success(self, async_client: AsyncClient):
        """Тест успешного получения категорий услуг"""
        with patch("src.aicrm.services.service_service.ServiceService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_categories.return_value = ["category1", "category2"]
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/services/categories")

            assert response.status_code == 200
            data = response.json()
            assert "categories" in data
            assert data["categories"] == ["category1", "category2"]

    # Products endpoints

    async def test_get_products_success(self, async_client: AsyncClient):
        """Тест успешного получения всех товаров"""
        response = await async_client.get("/ai-manager/products")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_active_products_success(self, async_client: AsyncClient):
        """Тест успешного получения активных товаров"""
        response = await async_client.get("/ai-manager/products/active")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_in_stock_products_success(self, async_client: AsyncClient):
        """Тест успешного получения товаров в наличии"""
        response = await async_client.get("/ai-manager/products/in-stock")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_product_by_id_success(self, async_client: AsyncClient):
        """Тест успешного получения товара по ID"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.name = "Test Product"
            mock_service.get_product_by_id.return_value = mock_product
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/products/1")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Product"

    async def test_get_product_by_id_not_found(self, async_client: AsyncClient):
        """Тест получения несуществующего товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_product_by_id.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/products/999")

            assert response.status_code == 404
            assert "Товар не найден" in response.json()["detail"]

    async def test_create_product_success(self, async_client: AsyncClient):
        """Тест успешного создания товара"""
        create_data = {
            "name": "New Test Product",
            "description": "New test description",
            "price": 500.00,
            "category": "test",
            "stock_quantity": 10,
            "is_active": True
        }

        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.name = "New Test Product"
            mock_product.description = "New test description"
            mock_product.price = 500.00
            mock_product.category = "test"
            mock_product.stock_quantity = 10
            mock_product.is_active = True
            mock_service.create_product.return_value = mock_product
            mock_service_class.return_value = mock_service

            response = await async_client.post("/ai-manager/products", json=create_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Test Product"

    async def test_update_product_success(self, async_client: AsyncClient):
        """Тест успешного обновления товара"""
        update_data = {
            "name": "Updated Product",
            "price": 600.00
        }

        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.name = "Updated Product"
            mock_product.price = 600.00
            mock_service.update_product.return_value = mock_product
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/products/1", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Product"

    async def test_update_product_not_found(self, async_client: AsyncClient):
        """Тест обновления несуществующего товара"""
        update_data = {"name": "Updated Product"}

        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_product.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/products/999", json=update_data)

            assert response.status_code == 404
            assert "Товар не найден" in response.json()["detail"]

    async def test_update_product_stock_success(self, async_client: AsyncClient):
        """Тест успешного обновления количества товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.stock_quantity = 20
            mock_service.update_stock.return_value = mock_product
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/products/1/stock", json={"stock_quantity": 20})

            assert response.status_code == 200
            data = response.json()
            assert data["stock_quantity"] == 20

    async def test_update_product_stock_not_found(self, async_client: AsyncClient):
        """Тест обновления количества несуществующего товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_stock.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.put("/ai-manager/products/999/stock", json={"stock_quantity": 20})

            assert response.status_code == 404
            assert "Товар не найден" in response.json()["detail"]

    async def test_delete_product_success(self, async_client: AsyncClient):
        """Тест успешного удаления товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_product.return_value = True
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/products/1")

            assert response.status_code == 204

    async def test_delete_product_not_found(self, async_client: AsyncClient):
        """Тест удаления несуществующего товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_product.return_value = False
            mock_service_class.return_value = mock_service

            response = await async_client.delete("/ai-manager/products/999")

            assert response.status_code == 404
            assert "Товар не найден" in response.json()["detail"]

    async def test_toggle_product_status_success(self, async_client: AsyncClient):
        """Тест успешного переключения статуса товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.is_active = False
            mock_service.toggle_product_status.return_value = mock_product
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/products/1/toggle")

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False

    async def test_toggle_product_status_not_found(self, async_client: AsyncClient):
        """Тест переключения статуса несуществующего товара"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.toggle_product_status.return_value = None
            mock_service_class.return_value = mock_service

            response = await async_client.patch("/ai-manager/products/999/toggle")

            assert response.status_code == 404
            assert "Товар не найден" in response.json()["detail"]

    async def test_get_product_categories_success(self, async_client: AsyncClient):
        """Тест успешного получения категорий товаров"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_categories.return_value = ["category1", "category2"]
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/products/categories")

            assert response.status_code == 200
            data = response.json()
            assert "categories" in data
            assert data["categories"] == ["category1", "category2"]

    async def test_get_low_stock_products_success(self, async_client: AsyncClient):
        """Тест успешного получения товаров с низким остатком"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_products = [MagicMock()]
            mock_service.get_low_stock_products.return_value = mock_products
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/products/low-stock?threshold=5")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_get_out_of_stock_products_success(self, async_client: AsyncClient):
        """Тест успешного получения товаров, которых нет в наличии"""
        with patch("src.aicrm.services.product_service.ProductService") as mock_service_class:
            mock_service = MagicMock()
            mock_products = [MagicMock()]
            mock_service.get_out_of_stock_products.return_value = mock_products
            mock_service_class.return_value = mock_service

            response = await async_client.get("/ai-manager/products/out-of-stock")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    # Validation tests

    async def test_create_prompt_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных при создании промпта"""
        invalid_data = {
            "name": "",  # Пустое имя
            "content": "Test content"
        }

        response = await async_client.post("/ai-manager/prompts", json=invalid_data)

        assert response.status_code == 422

    async def test_create_service_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных при создании услуги"""
        invalid_data = {
            "name": "Test Service",
            "price": -100.00  # Отрицательная цена
        }

        response = await async_client.post("/ai-manager/services", json=invalid_data)

        assert response.status_code == 422

    async def test_create_product_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных при создании товара"""
        invalid_data = {
            "name": "Test Product",
            "price": -50.00,  # Отрицательная цена
            "stock_quantity": -5  # Отрицательное количество
        }

        response = await async_client.post("/ai-manager/products", json=invalid_data)

        assert response.status_code == 422

    async def test_update_product_stock_validation_error(self, async_client: AsyncClient):
        """Тест валидации данных при обновлении количества товара"""
        invalid_data = {
            "stock_quantity": -10  # Отрицательное количество
        }

        response = await async_client.put("/ai-manager/products/1/stock", json=invalid_data)

        assert response.status_code == 422
