# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RecipeUOM(models.Model):
    _name = 'recipe.uom'
    _description = 'Recipe Unit of Measure'
    _order = 'name'

    name = fields.Char(string='Unit Name', required=True, help='Name of the unit (e.g., Cup, Gram, Liter)')
    code = fields.Char(string='Code', required=True, help='Short code for the unit (e.g., cup, g, l)')
    description = fields.Text(string='Description', help='Additional description of the unit')
    active = fields.Boolean(string='Active', default=True)
    recipe_id = fields.Many2one('recipe.recipe', string='Recipe', ondelete='cascade', 
                                help='Recipe this UOM belongs to. Leave empty for global UOMs available to all recipes.')
    is_global = fields.Boolean(string='Global UOM', compute='_compute_is_global', store=True,
                                help='Indicates if this UOM is available to all recipes')
    
    @api.depends('recipe_id')
    def _compute_is_global(self):
        for record in self:
            record.is_global = not record.recipe_id
    
    _sql_constraints = [
        ('code_recipe_unique', 'unique(code, recipe_id)', 'The code must be unique per recipe!'),
    ]

