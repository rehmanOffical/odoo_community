# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class IngredientList(models.Model):
    _name = 'ingredient.list'
    _description = 'Ingredient List'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    source_recipe_ids = fields.Many2many('recipe.recipe', string='Source Recipes')
    ingredient_ids = fields.One2many('ingredient.list.line', 'ingredient_list_id', string='Ingredients')
    notes = fields.Text(string='Notes')


class IngredientListLine(models.Model):
    _name = 'ingredient.list.line'
    _description = 'Ingredient List Line'
    _order = 'sequence, name'

    ingredient_list_id = fields.Many2one('ingredient.list', string='Ingredient List', required=True, ondelete='cascade')
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


class IngredientListWizard(models.TransientModel):
    _name = 'ingredient.list.wizard'
    _description = 'Ingredient List Wizard'

    # Legacy single-select support to avoid KeyError from old contexts/views
    recipe_id = fields.Many2one('recipe.recipe', string='Recipe (legacy)')
    recipe_ids = fields.Many2many('recipe.recipe', string='Recipes to Combine', required=True)
    name = fields.Char(string='Ingredient List Name', required=True, default='Ingredient List')

    @api.onchange('recipe_id')
    def _onchange_recipe_id(self):
        if self.recipe_id:
            self.recipe_ids = [(4, self.recipe_id.id)]

    def _normalize_unit(self, unit):
        """Normalize unit strings to canonical short codes used in selection."""
        if not unit:
            return 'piece'
        u = (unit or '').strip().lower()
        mapping = {
            'tablespoon': 'tbsp',
            'tbsp': 'tbsp',
            'teaspoon': 'tsp',
            'tsp': 'tsp',
            'kilogram': 'kg',
            'kg': 'kg',
            'gram': 'g',
            'g': 'g',
            'milliliter': 'ml',
            'ml': 'ml',
            'liter': 'l',
            'l': 'l',
            'ounce': 'oz',
            'oz': 'oz',
            'pound': 'lb',
            'lb': 'lb',
            'cup': 'cup',
            'piece': 'piece',
            'slice': 'slice',
            'clove': 'clove',
            'pinch': 'pinch',
            'dash': 'dash',
            'head': 'head',
            'bunch': 'bunch',
            'can': 'can',
            'bottle': 'bottle',
            'other': 'other',
        }
        return mapping.get(u, u or 'piece')

    def action_consolidate(self):
        self.ensure_one()
        # If legacy field used, promote it
        if not self.recipe_ids and self.recipe_id:
            self.recipe_ids = [(4, self.recipe_id.id)]
        if not self.recipe_ids:
            raise UserError('Please select at least one recipe to consolidate.')

        # Aggregate ingredients from all selected recipes
        from collections import OrderedDict
        grouped = OrderedDict()
        order = []
        for recipe in self.recipe_ids:
            for line in recipe.ingredient_ids:
                name_key = (line.name or '').strip().lower()
                unit_key = self._normalize_unit(line.unit)
                key = (name_key, unit_key)
                if key not in grouped:
                    grouped[key] = {
                        'name': line.name.strip() if line.name else '',
                        'quantity': 0.0,
                        'unit': unit_key,
                        'notes': []
                    }
                    order.append(key)
                grouped[key]['quantity'] += float(line.quantity or 0.0)
                if line.notes:
                    grouped[key]['notes'].append(line.notes)

        # Create ingredient list record
        ingredient_list = self.env['ingredient.list'].create({
            'name': self.name,
            'source_recipe_ids': [(6, 0, self.recipe_ids.ids)],
        })

        sequence = 10
        for key in order:
            data = grouped[key]
            self.env['ingredient.list.line'].create({
                'ingredient_list_id': ingredient_list.id,
                'name': data['name'],
                'quantity': data['quantity'],
                'unit': data['unit'],
                'notes': ', '.join(data['notes']) if data['notes'] else False,
                'sequence': sequence,
            })
            sequence += 10

        return {
            'type': 'ir.actions.act_window',
            'name': 'Ingredient List',
            'res_model': 'ingredient.list',
            'view_mode': 'form',
            'res_id': ingredient_list.id,
            'target': 'current',
        }

