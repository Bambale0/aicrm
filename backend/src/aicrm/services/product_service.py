"""
Сервис для управления товарами
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.product import Product


class ProductService:
    """Сервис для работы с товарами"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_products(self) -> List[Product]:
        """Получить все товары"""
        return self.db.query(Product).order_by(Product.category, Product.name).all()

    def get_active_products(self) -> List[Product]:
        """Получить активные товары"""
        return self.db.query(Product).filter(Product.is_active == True).order_by(Product.category, Product.name).all()

    def get_products_by_category(self, category: str) -> List[Product]:
        """Получить товары по категории"""
        return self.db.query(Product).filter(
            Product.category == category,
            Product.is_active == True
        ).order_by(Product.name).all()

    def get_in_stock_products(self) -> List[Product]:
        """Получить товары в наличии (stock_quantity > 0)"""
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock_quantity > 0
        ).order_by(Product.category, Product.name).all()

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получить товар по ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Получить товар по артикулу"""
        return self.db.query(Product).filter(Product.sku == sku).first()

    def create_product(self, name: str, description: str, price: float, category: str, stock_quantity: int = 0, **kwargs) -> Product:
        """Создать новый товар"""
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            stock_quantity=stock_quantity,
            **kwargs
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Обновить товар"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stock(self, product_id: int, new_quantity: int) -> Optional[Product]:
        """Обновить количество товара на складе"""
        return self.update_product(product_id, stock_quantity=new_quantity)

    def delete_product(self, product_id: int) -> bool:
        """Удалить товар"""
        product = self.get_product_by_id(product_id)
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()
        return True

    def toggle_product_status(self, product_id: int) -> Optional[Product]:
        """Переключить статус товара (активен/неактивен)"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None

        product.is_active = not product.is_active
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_categories(self) -> List[str]:
        """Получить список уникальных категорий товаров"""
        result = self.db.query(Product.category).distinct().all()
        return [row[0] for row in result]

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Получить товары с низким остатком на складе"""
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock_quantity <= threshold,
            Product.stock_quantity > 0
        ).order_by(Product.stock_quantity).all()

    def get_out_of_stock_products(self) -> List[Product]:
        """Получить товары, которых нет в наличии"""
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock_quantity == 0
        ).order_by(Product.name).all()
