# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    recipe_ids = fields.Many2many(
        'recipe.recipe',
        'recipe_recipe_sale_order_line_rel',
        'sale_order_line_id',
        'recipe_recipe_id',
        string='Recipes',
        help='Recipes associated with this order line'
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Override to create caterer list when quotation is converted to sales order"""
        res = super().action_confirm()
        
        # Check if caterer module is installed
        if 'caterer.list' not in self.env:
            return res
        
        # After confirmation, create caterer list with recipes from menu items
        for order in self:
            # Collect recipes from menu items linked to order line products
            try:
                # Collect recipes with their order line information
                recipe_data = []
                for order_line in order.order_line:
                    # Skip delivery charge lines
                    if order_line.product_id and order_line.product_id.default_code and order_line.product_id.default_code.startswith('DELIVERY-'):
                        continue
                    
                    # Get menu item from product default_code (format: MENU-{menu_item_id})
                    menu_item = self._get_menu_item_from_product(order_line.product_id)
                    if menu_item and menu_item.recipe_id:
                        recipe_data.append({
                            'recipe': menu_item.recipe_id,
                            'order_line': order_line,
                            'quantity': order_line.product_uom_qty or 1.0,
                            'menu_item': menu_item,
                        })
            except Exception as e:
                # Log error but continue
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning('Error collecting recipes from menu items for order %s: %s', order.name, str(e))
                continue
            
            if recipe_data:
                # Create caterer list using the same logic as the wizard
                caterer_list = self._create_caterer_from_recipes(order, recipe_data)
                if caterer_list:
                    # Set the caterer_list_id field if it exists (added by post_init_hook)
                    if hasattr(order, 'caterer_list_id'):
                        order.caterer_list_id = caterer_list.id
                
        return res
    
    def _get_menu_item_from_product(self, product):
        """Get menu item from product based on default_code (MENU-{id})"""
        # Check if menu.item model exists (menu_management module installed)
        if 'menu.item' not in self.env:
            return False
        
        if not product or not product.default_code:
            return False
        
        # Check if product code starts with MENU-
        if not product.default_code.startswith('MENU-'):
            return False
        
        try:
            # Extract menu item ID from default_code
            menu_item_id = int(product.default_code.replace('MENU-', ''))
            menu_item = self.env['menu.item'].browse(menu_item_id)
            if menu_item.exists():
                return menu_item
        except (ValueError, AttributeError):
            pass
        
        return False

    def _create_caterer_from_recipes(self, order, recipe_data):
        """Create a caterer list from recipes with scaled quantities based on order lines"""
        # Check if caterer module is installed
        if 'caterer.list' not in self.env:
            return False
        
        if not recipe_data:
            return False
        
        try:
            # Aggregate ingredients from all recipes with scaling
            from collections import OrderedDict
            grouped = OrderedDict()
            order_list = []
            all_recipe_ids = []
            
            for data in recipe_data:
                recipe = data['recipe']
                order_line = data['order_line']
                order_quantity = data['quantity']
                
                if not recipe.exists():
                    continue
                
                # Collect recipe IDs for the many2many field
                if recipe.id not in all_recipe_ids:
                    all_recipe_ids.append(recipe.id)
                
                # Calculate scaling factor
                # Scale based on order line quantity and servings
                # Priority: menu_item.serving_size > order note serving count > recipe servings
                recipe_servings = recipe.servings or 1
                menu_item = data.get('menu_item')
                
                # Get serving size from menu item if available
                if menu_item and menu_item.serving_size:
                    serving_size = menu_item.serving_size
                else:
                    # Try to get serving count from order note
                    serving_size = self._extract_serving_count(order)
                
                if serving_size:
                    # Scale by order quantity and serving size
                    # Formula: (order_quantity * serving_size) / recipe_servings
                    scale_factor = (order_quantity * serving_size) / recipe_servings
                else:
                    # Just scale by order quantity
                    scale_factor = order_quantity
                
                # Aggregate ingredients with scaling
                for ingredient_line in recipe.ingredient_ids:
                    if not ingredient_line.name:
                        continue
                    
                    name_key = (ingredient_line.name or '').strip().lower()
                    unit_key = self._normalize_unit(ingredient_line.unit)
                    key = (name_key, unit_key)
                    
                    if key not in grouped:
                        grouped[key] = {
                            'name': ingredient_line.name.strip() if ingredient_line.name else '',
                            'quantity': 0.0,
                            'unit': unit_key,
                            'notes': []
                        }
                        order_list.append(key)
                    
                    # Scale the ingredient quantity
                    scaled_quantity = float(ingredient_line.quantity or 0.0) * scale_factor
                    grouped[key]['quantity'] += scaled_quantity
                    
                    if ingredient_line.notes:
                        grouped[key]['notes'].append(ingredient_line.notes)
            
            # Only create caterer list if we have ingredients
            if not grouped:
                return False
            
            # Prepare notes with delivery information
            notes_parts = [f'Automatically created from Sales Order {order.name}']
            
            # Extract delivery information from order note
            delivery_info = self._extract_delivery_info(order)
            if delivery_info:
                notes_parts.append('\n\nDelivery Information:')
                notes_parts.extend(delivery_info)
            
            # Create caterer list with order reference as name
            caterer_name = f"Caterer - {order.name}"
            caterer_list = self.env['caterer.list'].create({
                'name': caterer_name,
                'source_recipe_ids': [(6, 0, all_recipe_ids)],
                'notes': '\n'.join(notes_parts),
            })
            
            # Create ingredient lines
            sequence = 10
            for key in order_list:
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
            
            return caterer_list
        except Exception as e:
            # Log error but don't break the order confirmation
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning('Failed to create caterer list for order %s: %s', order.name, str(e))
            return False
    
    def _extract_delivery_info(self, order):
        """Extract delivery information from order note"""
        if not order.note:
            return []
        
        delivery_info = []
        lines = order.note.split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                # Check if it's delivery-related information
                if any(keyword in line.lower() for keyword in ['delivery', 'serving', 'service type', 'special instructions']):
                    delivery_info.append(line)
        
        return delivery_info
    
    def _extract_serving_count(self, order):
        """Extract serving count from order note"""
        if not order.note:
            return None
        
        import re
        # Look for "Serving: X" pattern
        match = re.search(r'Serving:\s*(\d+)', order.note, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, AttributeError):
                pass
        
        return None

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

