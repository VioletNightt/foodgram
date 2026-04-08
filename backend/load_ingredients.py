import json
import os
import django

from recipes.models import Ingredient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()


def load_ingredients():
    try:
        with open('ingredients.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: 'ingredients.json' file not found.")
        return

    ingredients_to_create = []
    for item in data:
        ingredient = Ingredient(
            name=item['name'],
            measurement_unit=item['unit']
        )
        ingredients_to_create.append(ingredient)

    Ingredient.objects.bulk_create(ingredients_to_create,
                                   ignore_conflicts=True)
    print(f"Successfully loaded {len(ingredients_to_create)} ingredients.")


if __name__ == "__main__":
    load_ingredients()
