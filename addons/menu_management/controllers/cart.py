# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta


class MenuCartController(http.Controller):

    @http.route('/menu/cart', type='http', auth='public', website=True, sitemap=False)
    def cart(self, **kwargs):
        """Display the shopping cart page"""
        return request.render('menu_management.cart_page', {})

    @http.route('/menu/checkout', type='http', auth='public', website=True, sitemap=False)
    def checkout(self, **kwargs):
        """Display the checkout page"""
        return request.render('menu_management.checkout_page', {
            'delivery_charge': 200.0,  # Hardcoded delivery charge
        })

    @http.route('/menu/checkout/process', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def process_checkout(self, **post):
        """Process the checkout and redirect to confirmation"""
        # Get form data
        customer_name = post.get('customer_name', '').strip()
        customer_email = post.get('customer_email', '').strip()
        customer_phone = post.get('customer_phone', '').strip()
        delivery_address = post.get('delivery_address', '').strip()
        delivery_city = post.get('delivery_city', '').strip()
        delivery_state = post.get('delivery_state', '').strip()
        delivery_zip = post.get('delivery_zip', '').strip()
        delivery_date = post.get('delivery_date', '').strip()
        delivery_time = post.get('delivery_time', '').strip()
        special_instructions = post.get('special_instructions', '').strip()

        # Store order data in session
        request.session['order_data'] = {
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'delivery_address': delivery_address,
            'delivery_city': delivery_city,
            'delivery_state': delivery_state,
            'delivery_zip': delivery_zip,
            'delivery_date': delivery_date,
            'delivery_time': delivery_time,
            'special_instructions': special_instructions,
            'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        return request.redirect('/menu/checkout/confirmation')

    @http.route('/menu/checkout/confirmation', type='http', auth='public', website=True, sitemap=False)
    def confirmation(self, **kwargs):
        """Display the order confirmation page"""
        order_data = request.session.get('order_data', {})
        if not order_data:
            return request.redirect('/menu/cart')

        return request.render('menu_management.checkout_confirmation', {
            'order_data': order_data,
        })

    @http.route('/menu/cart/clear', type='json', auth='public', website=True, methods=['POST'], csrf=False)
    def clear_cart(self, **kwargs):
        """Clear the cart (handled by JavaScript localStorage)"""
        return {'success': True}
