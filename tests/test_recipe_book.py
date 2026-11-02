import sqlite3
import tempfile
import unittest
from pathlib import Path

from recipe_book.database import Database
from recipe_book.repository import RecipeRepository
from recipe_book.service import RecipeService


class RecipeBookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.sqlite3")
        self.service = RecipeService(RecipeRepository(self.database.connection))
        self.tomato = self.service.add_ingredient("Помидор", "Овощи", "шт.")
        self.cheese = self.service.add_ingredient("Сыр", "Молочные продукты", "г")
        self.recipe_id = self.service.create_recipe(
            "Быстрый салат",
            "Салаты",
            2,
            10,
            5,
            [(self.tomato, 2), (self.cheese, 30)],
            [("смешивание", "Смешать продукты.", 5)],
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temp_dir.cleanup()

    def test_search_filters_by_ingredient_category_operation_and_speed(self) -> None:
        self.assertEqual(len(self.service.search_recipes(ingredient="помидор")), 1)
        self.assertEqual(len(self.service.search_recipes(category="салат")), 1)
        self.assertEqual(len(self.service.search_recipes(ingredient_category="овощи")), 1)
        self.assertEqual(len(self.service.search_recipes(operation="смеш")), 1)
        self.assertEqual(len(self.service.search_recipes(speed="быстро")), 1)
        self.assertEqual(len(self.service.search_recipes(max_minutes=10)), 0)

    def test_recipe_details_include_ingredients_and_ordered_steps(self) -> None:
        recipe = self.service.get_recipe(self.recipe_id)

        self.assertIsNotNone(recipe)
        assert recipe is not None
        self.assertEqual(recipe.total_minutes, 15)
        self.assertEqual([item.ingredient.name for item in recipe.ingredients], ["Помидор", "Сыр"])
        self.assertEqual(recipe.steps[0].position, 1)
        self.assertEqual(recipe.steps[0].operation, "смешивание")

    def test_recipe_requires_ingredients_and_steps(self) -> None:
        with self.assertRaisesRegex(ValueError, "хотя бы один ингредиент"):
            self.service.create_recipe("Пустое блюдо", "Тест", 1, 0, 0, [], [("варка", "Варить", 1)])

        with self.assertRaisesRegex(ValueError, "хотя бы один шаг"):
            self.service.create_recipe("Без шагов", "Тест", 1, 0, 0, [(self.tomato, 1)], [])

    def test_duplicate_name_does_not_leave_partial_recipe(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.create_recipe(
                "Быстрый салат",
                "Другое",
                1,
                0,
                0,
                [(self.tomato, 1)],
                [("смешивание", "Смешать.", 0)],
            )

        self.assertEqual(len(self.service.search_recipes()), 1)


if __name__ == "__main__":
    unittest.main()
