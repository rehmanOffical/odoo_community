# -*- coding: utf-8 -*-

from . import models


def post_init_hook(env):
    """Add caterer_list_id field and view to sale.order if caterer module is installed"""
    try:
        if 'caterer.list' in env.registry:
            from odoo import fields
            
            SaleOrder = env.registry['sale.order']
            if 'caterer_list_id' not in SaleOrder._fields:
                # Create the field
                field = fields.Many2one(
                    comodel_name='caterer.list',
                    string='Caterer List',
                    readonly=True,
                    help='Caterer list automatically created when this order was confirmed'
                )
                # Use add_field utility which handles setup properly
                # First, we need to make it a manual field (x_ prefix) or use add_field
                # Since add_field requires x_ prefix for manual fields, we'll set it up manually
                setattr(SaleOrder, 'caterer_list_id', field)
                field.__set_name__(SaleOrder, 'caterer_list_id')
                SaleOrder._fields__['caterer_list_id'] = field
                field._toplevel = True
                
                # Setup the field on the model
                field.setup(SaleOrder)
                
                # Create the view dynamically
                view_arch = '''<xpath expr="//notebook" position="after">
                        <group string="Caterer" invisible="not caterer_list_id">
                            <field name="caterer_list_id" readonly="1" 
                                   options="{'no_create': True}"/>
                        </group>
                    </xpath>'''
                
                # Check if view already exists
                existing_view = env['ir.ui.view'].search([
                    ('name', '=', 'sale.order.form.recipe'),
                    ('model', '=', 'sale.order')
                ], limit=1)
                
                if not existing_view:
                    base_view = env.ref('sale.view_order_form', raise_if_not_found=False)
                    if base_view:
                        env['ir.ui.view'].sudo().create({
                            'name': 'sale.order.form.recipe',
                            'model': 'sale.order',
                            'inherit_id': base_view.id,
                            'arch': view_arch,
                            'type': 'form',
                        })
    except Exception as e:
        # Log error but don't break module installation
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning('Error in recipe post_init_hook: %s', str(e))