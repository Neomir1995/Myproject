# Книга рецептов

Учебное консольное приложение на Python для составления рецептов, учёта ингредиентов и поиска блюд. Данные сохраняются в SQLite. Интерфейс и дополнительные библиотеки не требуются.

## Запуск

Из корневой папки проекта:

```powershell
python -m recipe_book
```

При первом запуске приложение создаёт базу `~/.recipe_book.sqlite3` и добавляет несколько примеров. Для выхода выберите `0`.

## Возможности

- ингредиенты с категориями и единицами измерения;
- рецепты с количеством порций, временем подготовки и готовки;
- последовательность шагов: жарка, варка, смешивание и другие операции;
- поиск по названию блюда, ингредиенту, категории, способу готовки, скорости и максимальному времени;
- просмотр полного рецепта и добавление собственных ингредиентов и блюд;
- фильтрация также по категории ингредиентов (например, «овощи» или «специи»).

Требуется Python 3.10 или новее.

Скорость определяется по общему времени: быстро — до 20 минут, средне — от 21 до 60 минут, долго — больше 60 минут. Несколько фильтров поиска применяются одновременно.

## Структура классов

```mermaid
classDiagram
    class Ingredient {
        +int id
        +str name
        +str category
        +str unit
    }
    class Recipe {
        +int id
        +str name
        +str category
        +int servings
        +int prep_minutes
        +int cook_minutes
        +total_minutes
        +speed
    }
    class RecipeIngredient {
        +Ingredient ingredient
        +float amount
    }
    class RecipeStep {
        +int position
        +str operation
        +str description
        +int duration_minutes
    }
    class RecipeService {
        +add_ingredient()
        +create_recipe()
        +search_recipes()
        +get_recipe()
    }
    class RecipeRepository {
        +add_ingredient()
        +create_recipe()
        +search_recipes()
        +get_recipe()
    }
    Recipe "1" *-- "1..*" RecipeIngredient
    Recipe "1" *-- "1..*" RecipeStep
    RecipeIngredient "*" --> "1" Ingredient
    RecipeService --> RecipeRepository
    RecipeRepository --> SQLite
```

## Проверка

```powershell
python -m unittest discover -s tests -v
```
