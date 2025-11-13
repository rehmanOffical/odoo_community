# -*- coding: utf-8 -*-
{
    'name': 'Recipe Management',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Manage recipes with ingredients and instructions',
    'description': """
        Recipe Management Module
        =======================
        
        This module allows you to:
        * Create and manage recipes
        * Add ingredients with quantities
        * Write step-by-step instructions
        * Categorize recipes
        * Track preparation and cooking times
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/recipe_views.xml',
        'views/sale_order_views.xml',
        'data/recipe_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
