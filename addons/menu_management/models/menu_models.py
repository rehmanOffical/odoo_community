# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MenuCategory(models.Model):
    _name = 'menu.category'
    _description = 'Menu Category'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
    image_1920 = fields.Image('Category Image')
    item_count = fields.Integer('Items Count', compute='_compute_item_count')

    def _compute_item_count(self):
        for category in self:
            category.item_count = self.env['menu.item'].search_count(
                [('category_id', '=', category.id)])


class MenuAllergen(models.Model):
    _name = 'menu.allergen'
    _description = 'Allergen Information'

    name = fields.Char(required=True)
    description = fields.Text()


class MenuDietaryTag(models.Model):
    _name = 'menu.dietary.tag'
    _description = 'Dietary Restriction Tags'

    name = fields.Char(required=True)
    color = fields.Integer('Color Index')


class MenuItem(models.Model):
    _name = 'menu.item'
    _description = 'Menu Item'
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(required=True)
    category_id = fields.Many2one(
        'menu.category', required=True, ondelete='restrict', string='Category')
    code = fields.Char('Item Code')
    description = fields.Html('Description')
    short_description = fields.Text(
        'Short Description', help='Brief description for menu cards')
    image_1920 = fields.Image('Product Image')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_featured = fields.Boolean(
        'Featured Item', default=False, help='Show as featured on website')

    # Pricing & Units
    price = fields.Float(
        'Selling Price', digits='Product Price', required=True)
    cost_price = fields.Float(
        'Cost Price', digits='Product Price', help='Internal cost for profit calculation')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True,
                             default=lambda self: self.env['uom.uom'].search([('name', '=', 'Units')], limit=1) or self.env['uom.uom'].search([], limit=1))
    serving_size = fields.Integer(
        'Serves (Number of People)', default=1, help='How many people this dish serves')
    min_order_qty = fields.Float(
        'Minimum Order Quantity', default=1.0, digits='Product Unit')
    max_order_qty = fields.Float(
        'Maximum Order Quantity', digits='Product Unit', help='0 = no limit')

    # Timing Information
    prep_time = fields.Integer(
        'Preparation Time (minutes)', help='Time to prepare this dish')
    cooking_time = fields.Integer(
        'Cooking Time (minutes)', help='Time to cook this dish')
    total_time = fields.Integer(
        'Total Time (minutes)', compute='_compute_total_time', store=True)

    # Dietary & Allergen Information
    allergen_ids = fields.Many2many('menu.allergen', string='Allergens',
                                    help='List of allergens present in this dish')
    dietary_tag_ids = fields.Many2many('menu.dietary.tag', string='Dietary Tags',
                                       help='Vegetarian, Vegan, Halal, Gluten-Free, etc.')
    spice_level = fields.Selection([
        ('none', 'No Spice'),
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('hot', 'Hot'),
        ('extra_hot', 'Extra Hot')
    ], string='Spice Level', default='medium')
    is_vegetarian = fields.Boolean('Vegetarian')
    is_vegan = fields.Boolean('Vegan')
    is_halal = fields.Boolean('Halal', default=True)
    is_gluten_free = fields.Boolean('Gluten Free')

    # Ingredients & Nutrition
    ingredients = fields.Html(
        'Ingredients List', help='Detailed list of ingredients used')
    calories = fields.Integer('Calories (per serving)',
                              help='Approximate calories per serving')
    protein = fields.Float('Protein (grams)')
    carbs = fields.Float('Carbohydrates (grams)')
    fat = fields.Float('Fat (grams)')

    # Availability & Status
    available = fields.Boolean(
        'Available', default=True, help='Is this item currently available?')
    available_from = fields.Date('Available From Date')
    available_until = fields.Date('Available Until Date')
    is_new = fields.Boolean('New Item', default=False, help='Mark as new item')
    is_popular = fields.Boolean('Popular Item', default=False)

    # Additional Information
    tags = fields.Char(
        'Tags', help='Comma-separated tags for search and filtering')
    internal_notes = fields.Text(
        'Internal Notes', help='Notes visible only to staff')
    preparation_notes = fields.Text(
        'Preparation Notes', help='Special instructions for kitchen staff')
    customer_notes = fields.Text(
        'Customer Notes', help='Special information to display to customers')

    # Recipe Information
    recipe_id = fields.Many2one(
        'recipe.recipe', string='Recipe', 
        help='Link to the recipe for this menu item')

    # Related Information
    item_count = fields.Integer(
        'Total Orders', compute='_compute_item_count', store=False)
    rating = fields.Float('Average Rating', digits=(12, 2), default=0.0)
    review_count = fields.Integer('Number of Reviews', default=0)

    @api.depends('prep_time', 'cooking_time')
    def _compute_total_time(self):
        for item in self:
            item.total_time = (item.prep_time or 0) + (item.cooking_time or 0)

    def _compute_item_count(self):
        # This would be linked to orders if you have an order module
        for item in self:
            item.item_count = 0  # Placeholder - can link to order module later

    def action_open_recipe(self):
        """Open the linked recipe"""
        self.ensure_one()
        if not self.recipe_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recipe',
            'res_model': 'recipe.recipe',
            'res_id': self.recipe_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class RecipeRecipe(models.Model):
    _inherit = 'recipe.recipe'

    menu_item_ids = fields.One2many(
        'menu.item', 'recipe_id', string='Menu Items',
        help='Menu items that use this recipe')
    menu_item_count = fields.Integer(
        'Menu Items Count', compute='_compute_menu_item_count', store=False)

    def _compute_menu_item_count(self):
        for recipe in self:
            recipe.menu_item_count = len(recipe.menu_item_ids)

    def action_open_menu_items(self):
        """Open menu items that use this recipe"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Menu Items',
            'res_model': 'menu.item',
            'domain': [('recipe_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }
