# Simple Recipe Management Module

A clean and simple Odoo module for managing recipes with ingredients and step-by-step instructions.

## Features

- **Simple Recipe Management**: Create, edit, and organize recipes
- **Ingredient Tracking**: Add ingredients with quantities and units
- **Step-by-Step Instructions**: Detailed cooking instructions with timing
- **Categorization**: Organize recipes by category (Appetizer, Main Course, Dessert, etc.)
- **Time Management**: Track preparation and cooking times
- **Difficulty Levels**: Easy, Medium, Hard difficulty ratings
- **Rating System**: Rate recipes from 1-5 stars
- **Image Support**: Add photos to recipes
- **Serving Type**: Categorize recipes by serving style (Individual, Family, Party, etc.)
- **Import Functionality**: Import recipes from text, CSV files, or paste directly
- **Search & Filter**: Advanced search and filtering capabilities

## Models

### Recipe (`recipe.recipe`)
Main model containing recipe information:
- Name, description, category
- Preparation and cooking times
- Difficulty level and rating
- Servings and serving type
- Notes and recipe image

### Recipe Ingredient (`recipe.ingredient`)
Ingredients for each recipe:
- Ingredient name and quantity
- Unit of measurement
- Additional notes
- Sequence ordering

### Recipe Instruction (`recipe.instruction`)
Step-by-step cooking instructions:
- Instruction text
- Step sequence
- Duration and temperature
- Optional timing information

### Recipe Import Wizard (`recipe.import.wizard`)
Import functionality with dropdown options:
- Manual Entry
- Import from URL
- Import from File

## Installation

1. Copy the `recipe` folder to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the "Recipe Management" module
4. Access recipes from the main menu

## Usage

1. Navigate to **Recipes > All Recipes**
2. Create a new recipe by clicking "Create"
3. Fill in the basic information (name, category, difficulty, etc.)
4. Add ingredients in the "Ingredients" tab
5. Add step-by-step instructions in the "Instructions" tab
6. Use the "Import Recipe" button to import recipes from external sources
7. Save and enjoy your organized recipe collection!

## Import Options

The module includes a dropdown with multiple import options:
- **Text Import**: Paste recipe text directly into the form
- **Text File**: Upload a plain text file (.txt) with recipe data
- **CSV File**: Upload a CSV file with recipe ingredients
- **Import from URL**: Import from recipe websites (placeholder)
- **Import from File**: Upload recipe files (handles both CSV and text files)

### Text File Format

The text file should follow this format:
```
Recipe Name

Ingredients:
Ingredient Name - Quantity Unit
Flour - 2 cups
Sugar - 1 cup
```

### CSV File Format

The CSV file should have the following columns:
```csv
Ingredient,Quantity,Unit,Notes
Flour,2,cup,All-purpose
Sugar,1,cup,Granulated
Butter,0.5,cup,Unsalted
```

Or with lowercase column headers:
```csv
ingredient,quantity,unit,notes
Flour,2,cup,All-purpose
Sugar,1,cup,Granulated
```

## Security

The module includes proper access rights:
- Regular users can read, write, and create recipes
- System administrators have full access including deletion rights

## Technical Details

- **Odoo Version**: 19.0
- **Dependencies**: base
- **License**: LGPL-3
- **Category**: Productivity
- **No Demo Data**: Clean installation without sample data
