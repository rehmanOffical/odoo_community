# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CatererList(models.Model):
    _name = 'caterer.list'
    _description = 'Caterer'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    source_recipe_ids = fields.Many2many('recipe.recipe', string='Source Recipes')
    ingredient_ids = fields.One2many('caterer.list.line', 'caterer_list_id', string='Ingredients')
    notes = fields.Text(string='Notes')


class CatererListLine(models.Model):
    _name = 'caterer.list.line'
    _description = 'Caterer Line'
    _order = 'sequence, name'

    caterer_list_id = fields.Many2one('caterer.list', string='Caterer', required=True, ondelete='cascade')
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


class CatererListWizard(models.TransientModel):
    _name = 'caterer.list.wizard'
    _description = 'Caterer Wizard'

    # Legacy single-select support to avoid KeyError from old contexts/views
    recipe_id = fields.Many2one('recipe.recipe', string='Recipe (legacy)')
    recipe_ids = fields.Many2many('recipe.recipe', string='Recipes to Combine', required=True)
    name = fields.Char(string='Caterer Name', required=True, default='Caterer')

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

        # Create caterer record
        caterer_list = self.env['caterer.list'].create({
            'name': self.name,
            'source_recipe_ids': [(6, 0, self.recipe_ids.ids)],
        })

        sequence = 10
        for key in order:
            data = grouped[key]
            self.env['caterer.list.line'].create({
                'caterer_list_id': caterer_list.id,
                'name': data['name'],
                'quantity': data['quantity'],
                'unit': data['unit'],
                'notes': ', '.join(data['notes']) if data['notes'] else False,
                'sequence': sequence,
            })
            sequence += 10

        return {
            'type': 'ir.actions.act_window',
            'name': 'Caterer',
            'res_model': 'caterer.list',
            'view_mode': 'form',
            'res_id': caterer_list.id,
            'target': 'current',
        }

