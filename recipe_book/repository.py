import sqlite3
from collections.abc import Iterable

from .models import Ingredient, Recipe, RecipeIngredient, RecipeStep


class RecipeRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def add_ingredient(self, name: str, category: str, unit: str) -> int:
        cursor = self.connection.execute(
            "INSERT INTO ingredients (name, category, unit) VALUES (?, ?, ?)",
            (name, category, unit),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_ingredients(self) -> list[Ingredient]:
        rows = self.connection.execute(
            "SELECT id, name, category, unit FROM ingredients ORDER BY category, name"
        ).fetchall()
        return [self._ingredient(row) for row in rows]

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
        with self.connection:
            cursor = self.connection.execute(
                """INSERT INTO recipes
                   (name, category, servings, prep_minutes, cook_minutes)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, category, servings, prep_minutes, cook_minutes),
            )
            recipe_id = int(cursor.lastrowid)
            self.connection.executemany(
                """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount)
                   VALUES (?, ?, ?)""",
                ((recipe_id, ingredient_id, amount) for ingredient_id, amount in ingredients),
            )
            self.connection.executemany(
                """INSERT INTO recipe_steps
                   (recipe_id, position, operation, description, duration_minutes)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    (recipe_id, position, operation, description, duration)
                    for position, (operation, description, duration) in enumerate(steps, 1)
                ),
            )
        return recipe_id

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
        conditions: list[str] = []
        params: list[object] = []
        if name:
            conditions.append("instr(casefold(r.name), casefold(?)) > 0")
            params.append(name)
        if ingredient:
            conditions.append(
                """EXISTS (
                    SELECT 1 FROM recipe_ingredients ri
                    JOIN ingredients i ON i.id = ri.ingredient_id
                    WHERE ri.recipe_id = r.id AND instr(casefold(i.name), casefold(?)) > 0
                )"""
            )
            params.append(ingredient)
        if category:
            conditions.append("instr(casefold(r.category), casefold(?)) > 0")
            params.append(category)
        if ingredient_category:
            conditions.append(
                """EXISTS (
                    SELECT 1 FROM recipe_ingredients ri
                    JOIN ingredients i ON i.id = ri.ingredient_id
                    WHERE ri.recipe_id = r.id
                      AND instr(casefold(i.category), casefold(?)) > 0
                )"""
            )
            params.append(ingredient_category)
        if operation:
            conditions.append(
                """EXISTS (
                    SELECT 1 FROM recipe_steps s
                    WHERE s.recipe_id = r.id AND instr(casefold(s.operation), casefold(?)) > 0
                )"""
            )
            params.append(operation)
        if max_minutes is not None:
            conditions.append("(r.prep_minutes + r.cook_minutes) <= ?")
            params.append(max_minutes)
        if speed == "быстро":
            conditions.append("(r.prep_minutes + r.cook_minutes) <= 20")
        elif speed == "средне":
            conditions.append("(r.prep_minutes + r.cook_minutes) BETWEEN 21 AND 60")
        elif speed == "долго":
            conditions.append("(r.prep_minutes + r.cook_minutes) > 60")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.connection.execute(
            f"""SELECT r.id, r.name, r.category, r.servings, r.prep_minutes, r.cook_minutes
                FROM recipes r {where}
                ORDER BY r.name""",
            params,
        ).fetchall()
        recipes: list[Recipe] = []
        for row in rows:
            recipe = self.get_recipe(row["id"])
            if recipe is not None:
                recipes.append(recipe)
        return recipes

    def get_recipe(self, recipe_id: int) -> Recipe | None:
        row = self.connection.execute(
            """SELECT id, name, category, servings, prep_minutes, cook_minutes
               FROM recipes WHERE id = ?""",
            (recipe_id,),
        ).fetchone()
        if row is None:
            return None

        ingredient_rows = self.connection.execute(
            """SELECT i.id, i.name, i.category, i.unit, ri.amount
               FROM recipe_ingredients ri
               JOIN ingredients i ON i.id = ri.ingredient_id
               WHERE ri.recipe_id = ? ORDER BY i.name""",
            (recipe_id,),
        ).fetchall()
        step_rows = self.connection.execute(
            """SELECT position, operation, description, duration_minutes
               FROM recipe_steps WHERE recipe_id = ? ORDER BY position""",
            (recipe_id,),
        ).fetchall()
        return Recipe(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            servings=row["servings"],
            prep_minutes=row["prep_minutes"],
            cook_minutes=row["cook_minutes"],
            ingredients=tuple(
                RecipeIngredient(self._ingredient(ingredient_row), ingredient_row["amount"])
                for ingredient_row in ingredient_rows
            ),
            steps=tuple(
                RecipeStep(
                    step["position"],
                    step["operation"],
                    step["description"],
                    step["duration_minutes"],
                )
                for step in step_rows
            ),
        )

    @staticmethod
    def _ingredient(row: sqlite3.Row) -> Ingredient:
        return Ingredient(row["id"], row["name"], row["category"], row["unit"])
