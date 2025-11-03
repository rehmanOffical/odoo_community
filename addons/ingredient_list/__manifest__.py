# -*- coding: utf-8 -*-
{
    'name': 'Ingredient List',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Create consolidated ingredient lists from multiple recipes',
    'description': """
        Ingredient List Module
        =====================
        
        This module allows you to:
        * Create ingredient lists by combining ingredients from multiple recipes
        * Consolidate duplicate ingredients with the same name and units
        * Generate shopping lists or ingredient requirements for meal planning
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['recipe'],
    'data': [
        'security/ir.model.access.csv',
        'views/ingredient_list_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}


