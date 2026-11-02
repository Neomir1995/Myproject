import sqlite3
from pathlib import Path

from .database import Database
from .models import Recipe
from .repository import RecipeRepository
from .service import RecipeService

DEFAULT_INGREDIENTS = (
    ("Помидор", "Овощи", "шт."),
    ("Огурец", "Овощи", "шт."),
    ("Сыр", "Молочные продукты", "г"),
    ("Макароны", "Крупы и макароны", "г"),
    ("Куриное филе", "Мясо", "г"),
    ("Соль", "Специи", "г"),
    ("Перец", "Специи", "г"),
    ("Оливковое масло", "Соусы и масла", "мл"),
)


def seed_data(service: RecipeService) -> None:
    if service.search_recipes():
        return
    existing = {ingredient.name.casefold(): ingredient.id for ingredient in service.list_ingredients()}
    ingredient_ids = {}
    for name, category, unit in DEFAULT_INGREDIENTS:
        ingredient_ids[name] = existing.get(name.casefold()) or service.add_ingredient(name, category, unit)
    service.create_recipe(
        "Салат из овощей",
        "Салаты",
        2,
        10,
        0,
        [
            (ingredient_ids["Помидор"], 2),
            (ingredient_ids["Огурец"], 1),
            (ingredient_ids["Соль"], 2),
            (ingredient_ids["Оливковое масло"], 15),
        ],
        [("смешивание", "Нарезать овощи, смешать и заправить маслом.", 10)],
    )
    service.create_recipe(
        "Макароны с сыром",
        "Основные блюда",
        2,
        5,
        15,
        [
            (ingredient_ids["Макароны"], 200),
            (ingredient_ids["Сыр"], 80),
            (ingredient_ids["Соль"], 5),
        ],
        [
            ("варка", "Отварить макароны в подсоленной воде.", 12),
            ("смешивание", "Слить воду и перемешать макароны с тёртым сыром.", 3),
        ],
    )
    service.create_recipe(
        "Курица с овощами",
        "Основные блюда",
        2,
        15,
        35,
        [
            (ingredient_ids["Куриное филе"], 300),
            (ingredient_ids["Помидор"], 2),
            (ingredient_ids["Перец"], 2),
            (ingredient_ids["Оливковое масло"], 15),
        ],
        [
            ("нарезка", "Нарезать курицу и овощи.", 10),
            ("жарка", "Обжарить курицу на разогретом масле.", 15),
            ("тушение", "Добавить овощи и тушить до готовности.", 20),
        ],
    )


def run(database_path: Path | None = None) -> None:
    path = database_path or Path.home() / ".recipe_book.sqlite3"
    database = Database(path)
    service = RecipeService(RecipeRepository(database.connection))
    try:
        seed_data(service)
        _menu(service)
    finally:
        database.close()


def _menu(service: RecipeService) -> None:
    while True:
        print(
            "\n=== Книга рецептов ===\n"
            "1. Все рецепты\n"
            "2. Поиск рецептов\n"
            "3. Показать рецепт\n"
            "4. Добавить ингредиент\n"
            "5. Создать рецепт\n"
            "0. Выход"
        )
        choice = input("Выберите действие: ").strip()
        try:
            if choice == "1":
                _print_recipes(service.search_recipes())
            elif choice == "2":
                _search(service)
            elif choice == "3":
                recipe = service.get_recipe(_read_int("ID рецепта: "))
                if recipe is None:
                    print("Рецепт не найден.")
                else:
                    _print_recipe(recipe)
            elif choice == "4":
                ingredient_id = service.add_ingredient(
                    input("Название: "),
                    input("Категория (например, овощи, мясо, специи): "),
                    input("Единица измерения: "),
                )
                print(f"Ингредиент добавлен, ID: {ingredient_id}.")
            elif choice == "5":
                _create_recipe(service)
            elif choice == "0":
                return
            else:
                print("Нет такого пункта меню.")
        except (ValueError, KeyError, sqlite3.IntegrityError) as error:
            print(f"Ошибка: {error}")


def _search(service: RecipeService) -> None:
    print("Оставьте поле пустым, если фильтр не нужен.")
    name = input("Название блюда: ").strip() or None
    ingredient = input("Ингредиент: ").strip() or None
    category = input("Категория блюда: ").strip() or None
    ingredient_category = input("Категория ингредиента: ").strip() or None
    operation = input("Способ приготовления (жарка, варка, смешивание...): ").strip() or None
    speed = input("Скорость (быстро / средне / долго): ").strip() or None
    max_text = input("Максимальное время в минутах: ").strip()
    max_minutes = int(max_text) if max_text else None
    _print_recipes(
        service.search_recipes(
            name=name,
            ingredient=ingredient,
            category=category,
            ingredient_category=ingredient_category,
            operation=operation,
            speed=speed,
            max_minutes=max_minutes,
        )
    )


def _create_recipe(service: RecipeService) -> None:
    print("\nДоступные ингредиенты:")
    ingredients = service.list_ingredients()
    for ingredient in ingredients:
        print(f"  {ingredient.id}. {ingredient.name} ({ingredient.category}, {ingredient.unit})")
    recipe_ingredients: list[tuple[int, float]] = []
    while True:
        ingredient_text = input("ID ингредиента (пусто — закончить): ").strip()
        if not ingredient_text:
            break
        ingredient_id = int(ingredient_text)
        amount = float(input("Количество: "))
        recipe_ingredients.append((ingredient_id, amount))

    steps: list[tuple[str, str, int]] = []
    while True:
        operation = input("Операция шага (пусто — закончить): ").strip()
        if not operation:
            break
        description = input("Описание: ").strip()
        duration = _read_int("Длительность шага, минут: ")
        steps.append((operation, description, duration))

    recipe_id = service.create_recipe(
        name=input("Название блюда: "),
        category=input("Категория блюда: "),
        servings=_read_int("Количество порций: "),
        prep_minutes=_read_int("Время подготовки, минут: "),
        cook_minutes=_read_int("Время готовки, минут: "),
        ingredients=recipe_ingredients,
        steps=steps,
    )
    print(f"Рецепт создан, ID: {recipe_id}.")


def _print_recipes(recipes: list[Recipe]) -> None:
    if not recipes:
        print("Рецепты не найдены.")
        return
    for recipe in recipes:
        print(
            f"{recipe.id}. {recipe.name} — {recipe.category}; "
            f"{recipe.total_minutes} мин. ({recipe.speed}), порций: {recipe.servings}"
        )


def _print_recipe(recipe: Recipe) -> None:
    print(
        f"\n{recipe.name} [{recipe.category}]\n"
        f"Порций: {recipe.servings}; подготовка: {recipe.prep_minutes} мин.; "
        f"готовка: {recipe.cook_minutes} мин.; всего: {recipe.total_minutes} мин."
    )
    print("Ингредиенты:")
    for item in recipe.ingredients:
        print(f"  • {item.ingredient.name}: {item.amount:g} {item.ingredient.unit}")
    print("Приготовление:")
    for step in recipe.steps:
        print(
            f"  {step.position}. {step.operation.capitalize()} "
            f"({step.duration_minutes} мин.) — {step.description}"
        )


def _read_int(prompt: str) -> int:
    return int(input(prompt))
