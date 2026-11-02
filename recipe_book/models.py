from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    id: int
    name: str
    category: str
    unit: str


@dataclass(frozen=True)
class RecipeIngredient:
    ingredient: Ingredient
    amount: float


@dataclass(frozen=True)
class RecipeStep:
    position: int
    operation: str
    description: str
    duration_minutes: int


@dataclass(frozen=True)
class Recipe:
    id: int
    name: str
    category: str
    servings: int
    prep_minutes: int
    cook_minutes: int
    ingredients: tuple[RecipeIngredient, ...] = ()
    steps: tuple[RecipeStep, ...] = ()

    @property
    def total_minutes(self) -> int:
        return self.prep_minutes + self.cook_minutes

    @property
    def speed(self) -> str:
        if self.total_minutes <= 20:
            return "быстро"
        if self.total_minutes <= 60:
            return "средне"
        return "долго"
