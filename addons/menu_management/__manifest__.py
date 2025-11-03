# -*- coding: utf-8 -*-
{
    'name': 'Menu Management',
    'version': '1.1.0',
    'summary': 'Store and publish menu items',
    'category': 'Website',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/website_menu_templates.xml',
        'data/menu_demo.xml',
        'data/website_menu_link.xml',
    ],
    'installable': True,
    'application': False,
}
