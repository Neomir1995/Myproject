from collections.abc import Iterable

from .models import Ingredient, Recipe
from .repository import RecipeRepository


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    def add_ingredient(self, name: str, category: str, unit: str) -> int:
        self._required(name, "Название ингредиента")
        self._required(category, "Категория")
        self._required(unit, "Единица измерения")
        return self.repository.add_ingredient(name.strip(), category.strip(), unit.strip())

    def list_ingredients(self) -> list[Ingredient]:
        return self.repository.list_ingredients()

    def create_recipe(
        self,
        name: str,
        category: str,
        servings: int,
        prep_minutes: int,
        cook_minutes: int,
        ingredients: Iterable[tuple[int, float]],
        steps: Iterable[tuple[str, str, int]],
    ) -> int:
        self._required(name, "Название блюда")
        self._required(category, "Категория")
        ingredients = list(ingredients)
        steps = list(steps)
        if servings <= 0:
            raise ValueError("Количество порций должно быть больше нуля.")
        if prep_minutes < 0 or cook_minutes < 0:
            raise ValueError("Время приготовления не может быть отрицательным.")
        if not ingredients:
            raise ValueError("Добавьте хотя бы один ингредиент.")
        if not steps:
            raise ValueError("Добавьте хотя бы один шаг приготовления.")
        for ingredient_id, amount in ingredients:
            if ingredient_id <= 0 or amount <= 0:
                raise ValueError("Ингредиент и его количество должны быть указаны корректно.")
        for operation, description, duration in steps:
            self._required(operation, "Операция")
            self._required(description, "Описание шага")
            if duration < 0:
                raise ValueError("Длительность шага не может быть отрицательной.")

        return self.repository.create_recipe(
            name.strip(),
            category.strip(),
            servings,
            prep_minutes,
            cook_minutes,
            ingredients,
            ((operation.strip(), description.strip(), duration) for operation, description, duration in steps),
        )

    def search_recipes(
        self,
        name: str | None = None,
        ingredient: str | None = None,
        category: str | None = None,
        ingredient_category: str | None = None,
        operation: str | None = None,
        max_minutes: int | None = None,
        speed: str | None = None,
    ) -> list[Recipe]:
        if max_minutes is not None and max_minutes < 0:
            raise ValueError("Максимальное время не может быть отрицательным.")
        if speed not in (None, "быстро", "средне", "долго"):
            raise ValueError("Скорость должна быть: быстро, средне или долго.")
        return self.repository.search_recipes(
            name=name.strip() if name else None,
            ingredient=ingredient.strip() if ingredient else None,
            category=category.strip() if category else None,
            ingredient_category=(
                ingredient_category.strip() if ingredient_category else None
            ),
            operation=operation.strip() if operation else None,
            max_minutes=max_minutes,
            speed=speed,
        )

    def get_recipe(self, recipe_id: int) -> Recipe | None:
        return self.repository.get_recipe(recipe_id)

    @staticmethod
    def _required(value: str, label: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{label}: поле не должно быть пустым.")
