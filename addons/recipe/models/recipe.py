# -*- coding: utf-8 -*-

import base64
import csv
import io
from odoo import models, fields, api
from odoo.exceptions import UserError


class Recipe(models.Model):
    _name = 'recipe.recipe'
    _description = 'Recipe'
    _order = 'name'

    name = fields.Char(string='Recipe Name', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('appetizer', 'Appetizer'),
        ('main_course', 'Main Course'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('snack', 'Snack'),
        ('other', 'Other')
    ], string='Category', default='main_course')
    
    # Time fields
    prep_time = fields.Integer(string='Preparation Time (minutes)')
    cook_time = fields.Integer(string='Cooking Time (minutes)')
    total_time = fields.Integer(string='Total Time (minutes)', compute='_compute_total_time', store=True)
    
    # Servings
    servings = fields.Integer(string='Servings', default=1)
    serving_type = fields.Selection([
        ('individual', 'Individual'),
        ('couple', 'Couple'),
        ('family', 'Family'),
        ('small_group', 'Small Group'),
        ('large_group', 'Large Group'),
        ('party', 'Party'),
        ('buffet', 'Buffet'),
        ('other', 'Other')
    ], string='Serving Type', default='family')
    
    # Ingredients
    ingredient_ids = fields.One2many('recipe.ingredient', 'recipe_id', string='Ingredients')
    
    # Instructions
    instruction_ids = fields.One2many('recipe.instruction', 'recipe_id', string='Instructions')
    
    # Additional fields
    difficulty = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], string='Difficulty Level', default='easy')
    
    rating = fields.Float(string='Rating', digits=(2, 1))
    notes = fields.Text(string='Notes')
    
    # Image
    image = fields.Binary(string='Recipe Image')
    
    active = fields.Boolean(string='Active', default=True)

    @api.depends('prep_time', 'cook_time')
    def _compute_total_time(self):
        for record in self:
            record.total_time = (record.prep_time or 0) + (record.cook_time or 0)

    def action_import_recipe(self):
        """Action to import recipe from external source"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Recipe',
            'res_model': 'recipe.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_recipe_id': self.id},
        }



class RecipeIngredient(models.Model):
    _name = 'recipe.ingredient'
    _description = 'Recipe Ingredient'
    _order = 'sequence, name'

    recipe_id = fields.Many2one('recipe.recipe', string='Recipe', required=True, ondelete='cascade')
    name = fields.Char(string='Ingredient Name', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit = fields.Selection([
        ('cup', 'Cup'),
        ('tbsp', 'Tablespoon'),
        ('tsp', 'Teaspoon'),
        ('oz', 'Ounce'),
        ('lb', 'Pound'),
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('piece', 'Piece'),
        ('slice', 'Slice'),
        ('clove', 'Clove'),
        ('pinch', 'Pinch'),
        ('dash', 'Dash'),
        ('head', 'Head'),
        ('bunch', 'Bunch'),
        ('can', 'Can'),
        ('bottle', 'Bottle'),
        ('other', 'Other')
    ], string='Unit', required=True, default='piece')
    notes = fields.Char(string='Notes')
    sequence = fields.Integer(string='Sequence', default=10)


class RecipeInstruction(models.Model):
    _name = 'recipe.instruction'
    _description = 'Recipe Instruction'
    _order = 'sequence'

    recipe_id = fields.Many2one('recipe.recipe', string='Recipe', required=True, ondelete='cascade')
    step = fields.Text(string='Instruction Step', required=True)
    sequence = fields.Integer(string='Step Number', required=True)
    duration = fields.Integer(string='Duration (minutes)')
    temperature = fields.Char(string='Temperature')


class RecipeImportWizardLine(models.TransientModel):
    _name = 'recipe.import.wizard.line'
    _description = 'Recipe Import Wizard Line'

    wizard_id = fields.Many2one('recipe.import.wizard', string='Wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit = fields.Selection([
        ('cup', 'Cup'),
        ('tbsp', 'Tablespoon'),
        ('tsp', 'Teaspoon'),
        ('oz', 'Ounce'),
        ('lb', 'Pound'),
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('piece', 'Piece'),
        ('slice', 'Slice'),
        ('clove', 'Clove'),
        ('pinch', 'Pinch'),
        ('dash', 'Dash'),
        ('head', 'Head'),
        ('bunch', 'Bunch'),
        ('can', 'Can'),
        ('bottle', 'Bottle'),
        ('other', 'Other')
    ], string='UOM', required=True, default='piece')
    notes = fields.Char(string='Notes')
    sequence = fields.Integer(string='Sequence', default=10)


class RecipeImportWizard(models.TransientModel):
    _name = 'recipe.import.wizard'
    _description = 'Recipe Import Wizard'

    recipe_id = fields.Many2one('recipe.recipe', string='Recipe')
    import_source = fields.Selection([
        ('text', 'Text'),
        ('text_file', 'Text File'),
        ('csv', 'CSV File'),
    ], string='Import Source', default='text', required=True)
    
    url = fields.Char(string='Recipe URL')
    file_data = fields.Binary(string='Recipe File')
    file_name = fields.Char(string='File Name')
    
    import_data = fields.Text(string='Recipe Text', help='Paste recipe text in the format:\nRecipe Name\n\nIngredients:\nIngredient - Quantity\n...')
    
    # Preview fields
    parsed_recipe_name = fields.Char(string='Recipe Name', readonly=True)
    parsed_ingredients = fields.Text(string='Ingredients Preview', readonly=True)
    show_preview = fields.Boolean(string='Show Preview', default=False)
    created_recipe_id = fields.Many2one('recipe.recipe', string='Created Recipe', readonly=True)
    
    # Interactive preview fields
    preview_ingredient_ids = fields.One2many('recipe.import.wizard.line', 'wizard_id', string='Ingredients')

    def action_import(self):
        """Import recipe data"""
        if self.import_source == 'text':
            return self._import_from_text()
        elif self.import_source == 'text_file':
            return self._import_from_text_file()
        elif self.import_source == 'csv':
            return self._import_from_csv()
        
    def action_parse_and_preview(self):
        """Parse recipe text and show preview"""
        if not self.import_data:
            raise UserError("Please provide recipe text to import.")
        
        try:
            recipe_data = self._parse_recipe_text(self.import_data)
            
            # Clear existing preview lines
            self.preview_ingredient_ids.unlink()
            
            # Create preview lines
            preview_lines = []
            for i, ingredient in enumerate(recipe_data['ingredients']):
                preview_lines.append({
                    'wizard_id': self.id,
                    'name': ingredient['name'],
                    'quantity': ingredient['quantity'],
                    'unit': ingredient['unit'],
                    'notes': ingredient['notes'],
                    'sequence': (i + 1) * 10,
                })
            
            # Create the preview lines
            self.env['recipe.import.wizard.line'].create(preview_lines)
            
            # Update preview fields
            self.write({
                'parsed_recipe_name': recipe_data['name'],
                'parsed_ingredients': self._format_ingredients_preview(recipe_data['ingredients']),
                'show_preview': True,
            })
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recipe Import Preview',
                'res_model': 'recipe.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        except Exception as e:
            raise UserError(f"Error parsing recipe: {str(e)}")
    
    def action_save_recipe(self):
        """Save the parsed recipe"""
        if not self.parsed_recipe_name:
            raise UserError("No recipe data to save.")
        
        try:
            # Create recipe from preview lines
            recipe = self._create_recipe_from_preview()
            
            self.write({
                'created_recipe_id': recipe.id,
                'show_preview': False,
            })
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recipe Imported Successfully',
                'res_model': 'recipe.recipe',
                'res_id': recipe.id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            raise UserError(f"Error saving recipe: {str(e)}")
    
    def _create_recipe_from_preview(self):
        """Create recipe from edited preview lines"""
        # Create recipe
        recipe = self.env['recipe.recipe'].create({
            'name': self.parsed_recipe_name,
            'category': 'main_course',  # Default category
            'difficulty': 'easy',  # Default difficulty
            'servings': 4,  # Default servings
            'serving_type': 'family',  # Default serving type
            'active': True,
        })
        
        # Create ingredients from preview lines
        for line in self.preview_ingredient_ids:
            self.env['recipe.ingredient'].create({
                'recipe_id': recipe.id,
                'name': line.name,
                'quantity': line.quantity,
                'unit': line.unit,
                'notes': line.notes,
                'sequence': line.sequence,
            })
        
        return recipe
    
    def _format_ingredients_preview(self, ingredients):
        """Format ingredients for preview display"""
        preview_lines = []
        for ingredient in ingredients:
            preview_lines.append(f"• {ingredient['name']} - {ingredient['quantity']} {ingredient['unit']}")
        return '\n'.join(preview_lines)
    
    def _import_from_text(self):
        """Import recipe from text format - redirect to preview"""
        return self.action_parse_and_preview()
    
    def _parse_recipe_text(self, text):
        """Parse recipe text and extract structured data"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        recipe_data = {
            'name': '',
            'ingredients': []
        }
        
        current_section = None
        ingredient_section = False
        
        for line in lines:
            # Check if this is a recipe name (first non-empty line that's not "Ingredients:")
            if not recipe_data['name'] and line != 'Ingredients:' and not ingredient_section:
                recipe_data['name'] = line
                continue
            
            # Check if we're entering ingredients section
            if line == 'Ingredients:':
                ingredient_section = True
                continue
            
            # Parse ingredients
            if ingredient_section and line:
                ingredient_data = self._parse_ingredient_line(line)
                if ingredient_data:
                    recipe_data['ingredients'].append(ingredient_data)
        
        if not recipe_data['name']:
            raise UserError("Could not find recipe name in the text.")
        
        return recipe_data
    
    def _parse_ingredient_line(self, line):
        """Parse a single ingredient line"""
        # Look for pattern: "Ingredient - Quantity" or "Ingredient – Quantity"
        import re
        
        # Try different separators
        separators = ['–', '-', '—']
        
        for sep in separators:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    ingredient_name = parts[0].strip()
                    quantity_text = parts[1].strip()
                    
                    # Parse quantity and unit
                    quantity, unit = self._parse_quantity(quantity_text)
                    
                    return {
                        'name': ingredient_name,
                        'quantity': quantity,
                        'unit': unit,
                        'notes': ''
                    }
        
        # If no separator found, treat the whole line as ingredient name
        return {
            'name': line,
            'quantity': 1.0,
            'unit': 'piece',
            'notes': ''
        }
    
    def _parse_quantity(self, quantity_text):
        """Parse quantity text to extract number and unit"""
        import re
        
        # Remove common words
        quantity_text = quantity_text.replace('to taste', '').strip()
        
        # Try to extract number and unit
        # Pattern for numbers with units - prioritize specific units over generic ones
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l|oz|lb|cup|tbsp|tsp|piece|slice|clove|pinch|dash|head|bunch|can|bottle)',
            r'(\d+(?:\.\d+)?)\s*(large|small|medium)',
            r'(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, quantity_text.lower())
            if match:
                quantity = float(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 else 'piece'
                
                # Normalize units
                unit_mapping = {
                    'tablespoon': 'tbsp',
                    'teaspoon': 'tsp',
                    'kilogram': 'kg',
                    'gram': 'g',
                    'milliliter': 'ml',
                    'liter': 'l',
                    'ounce': 'oz',
                    'pound': 'lb',
                    'large': 'piece',
                    'small': 'piece',
                    'medium': 'piece',
                    'bunch': 'piece',  # Temporary workaround
                    'can': 'piece',    # Temporary workaround
                    'bottle': 'piece', # Temporary workaround
                }
                
                unit = unit_mapping.get(unit, unit)
                
                return quantity, unit
        
        # Default fallback
        return 1.0, 'piece'
    
    def _create_recipe(self, recipe_data):
        """Create recipe and ingredients from parsed data"""
        # Create recipe
        recipe = self.env['recipe.recipe'].create({
            'name': recipe_data['name'],
            'category': 'main_course',  # Default category
            'difficulty': 'easy',  # Default difficulty
            'servings': 4,  # Default servings
            'serving_type': 'family',  # Default serving type
            'active': True,
        })
        
        # Create ingredients
        for i, ingredient_data in enumerate(recipe_data['ingredients']):
            self.env['recipe.ingredient'].create({
                'recipe_id': recipe.id,
                'name': ingredient_data['name'],
                'quantity': ingredient_data['quantity'],
                'unit': ingredient_data['unit'],
                'notes': ingredient_data['notes'],
                'sequence': (i + 1) * 10,
            })
        
        return recipe
    
    def _import_from_url(self):
        """Import from URL - placeholder for future implementation"""
        # This would typically fetch data from a recipe website
        # For now, just return to form
        return {'type': 'ir.actions.act_window_close'}
    
    def _import_from_file(self):
        """Import from file - handle different file types"""
        if not self.file_data:
            raise UserError("Please provide a file to import.")
        
        # Determine file type from extension
        if self.file_name and self.file_name.lower().endswith('.csv'):
            return self._import_from_csv()
        else:
            return self._import_from_text_file()
    
    def _import_from_csv(self):
        """Import recipe from CSV file"""
        if not self.file_data:
            raise UserError("Please provide a CSV file to import.")
        
        try:
            # Decode the file
            file_content = base64.b64decode(self.file_data).decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            recipe_data = {
                'name': '',
                'ingredients': []
            }
            
            # First row should contain recipe name
            rows = list(csv_reader)
            if not rows:
                raise UserError("CSV file is empty.")
            
            # Check if CSV has a header row for recipe info
            # Expected CSV format:
            # Name: Recipe Name
            # Ingredient,Quantity,Unit,Notes
            # or
            # Ingredient,Quantity,Unit,Notes (if recipe name is provided)
            
            # Try to parse recipe name
            recipe_name = self.file_name or 'Imported Recipe'
            if recipe_name.endswith('.csv'):
                recipe_name = recipe_name[:-4]
            
            # Parse ingredients from CSV
            for row in rows:
                ingredient_name = row.get('Ingredient', row.get('ingredient', '')).strip()
                if not ingredient_name:
                    continue
                
                quantity = float(row.get('Quantity', row.get('quantity', 1)))
                unit = row.get('Unit', row.get('unit', 'piece')).strip()
                notes = row.get('Notes', row.get('notes', '')).strip()
                
                recipe_data['ingredients'].append({
                    'name': ingredient_name,
                    'quantity': quantity,
                    'unit': unit,
                    'notes': notes
                })
            
            if recipe_data['name']:
                # Name found in CSV
                pass
            else:
                recipe_data['name'] = recipe_name
            
            # Show preview with parsed data
            return self._show_preview_with_data(recipe_data)
            
        except csv.Error as e:
            raise UserError(f"Error reading CSV file: {str(e)}")
        except Exception as e:
            raise UserError(f"Error importing CSV file: {str(e)}")
    
    def _import_from_text_file(self):
        """Import recipe from text file"""
        if not self.file_data:
            raise UserError("Please provide a text file to import.")
        
        try:
            # Decode the file
            file_content = base64.b64decode(self.file_data).decode('utf-8')
            
            # Parse as text
            recipe_data = self._parse_recipe_text(file_content)
            
            # Show preview with parsed data
            return self._show_preview_with_data(recipe_data)
            
        except Exception as e:
            raise UserError(f"Error importing text file: {str(e)}")
    
    def _show_preview_with_data(self, recipe_data):
        """Show preview with recipe data"""
        # Clear existing preview lines
        self.preview_ingredient_ids.unlink()
        
        # Create preview lines
        preview_lines = []
        for i, ingredient in enumerate(recipe_data['ingredients']):
            preview_lines.append({
                'wizard_id': self.id,
                'name': ingredient['name'],
                'quantity': ingredient['quantity'],
                'unit': ingredient['unit'],
                'notes': ingredient.get('notes', ''),
                'sequence': (i + 1) * 10,
            })
        
        # Create the preview lines
        self.env['recipe.import.wizard.line'].create(preview_lines)
        
        # Update preview fields
        self.write({
            'parsed_recipe_name': recipe_data['name'],
            'parsed_ingredients': self._format_ingredients_preview(recipe_data['ingredients']),
            'show_preview': True,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recipe Import Preview',
            'res_model': 'recipe.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }