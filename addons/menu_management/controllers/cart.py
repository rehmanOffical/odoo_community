# -*- coding: utf-8 -*-
import json
import re
import traceback
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class MenuCartController(http.Controller):

    def _log_message(self, name, level, message, func='process_checkout', line=0, path='/menu/checkout/process'):
        """Utility to log messages with required fields."""
        request.env['ir.logging'].sudo().create({
            'name': name,
            'type': 'server',
            'dbname': request.env.cr.dbname,
            'level': level,
            'message': message,
            'path': path,
            'func': func,
            'line': line,
        })

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

    @http.route('/menu/checkout/process', type='http', auth='public', website=True, csrf=False)
    def process_checkout(self, **post):
        """Process the checkout and create a sales order"""
        # Only allow POST requests
        if request.httprequest.method != 'POST':
            return request.redirect('/menu/cart')

        try:
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

            # Get cart data from request (passed via hidden field or session)
            cart_data_json = post.get('cart_data', '[]')
            try:
                cart_data = json.loads(
                    cart_data_json) if cart_data_json else []
            except Exception as e:
                self._log_message(
                    name='Menu Checkout',
                    level='error',
                    message=f'Error parsing cart data: {str(e)}',
                    func='process_checkout'
                )
                cart_data = []

            if not cart_data:
                return request.redirect('/menu/cart')

            # Create or get partner
            partner = self._get_or_create_partner(
                customer_name, customer_email, customer_phone)

            # Create sales order
            sale_order = self._create_sale_order(
                partner=partner,
                cart_data=cart_data,
                delivery_address=delivery_address,
                delivery_city=delivery_city,
                delivery_state=delivery_state,
                delivery_zip=delivery_zip,
                delivery_date=delivery_date,
                delivery_time=delivery_time,
                special_instructions=special_instructions,
            )

            # Store order data in session for confirmation page
            request.session['order_data'] = {
                'order_id': sale_order.id,
                'order_name': sale_order.name,
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
                'total_amount': sale_order.amount_total,
            }

            return request.redirect('/menu/checkout/confirmation')
        except Exception as e:
            # Log the error
            error_msg = f"Error in checkout process: {str(e)}\n{traceback.format_exc()}"
            self._log_message(
                name='Menu Checkout Error',
                level='error',
                message=error_msg,
                func='process_checkout'
            )
            # Return a simple error message page
            error_html = f"""
            <html>
            <head><title>Order Error</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>Order Processing Error</h1>
                <p>An error occurred while processing your order. Please try again.</p>
                <p style="color: #666; font-size: 12px;">Error: {str(e)}</p>
                <a href="/menu/cart" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">Back to Cart</a>
            </body>
            </html>
            """
            return error_html

    def _get_or_create_partner(self, name, email, phone):
        """Get or create a partner (customer)"""
        partner_obj = request.env['res.partner'].sudo()

        # Try to find existing partner by email
        if email:
            partner = partner_obj.search([('email', '=', email)], limit=1)
            if partner:
                # Update partner info if needed
                if name and not partner.name:
                    partner.name = name
                if phone and not partner.phone:
                    partner.phone = phone
                return partner

        # Create new partner
        partner_vals = {
            'name': name or 'Customer',
            'email': email or False,
            'phone': phone or False,
            'customer_rank': 1,
        }
        return partner_obj.create(partner_vals)

    def _create_sale_order(self, partner, cart_data, delivery_address, delivery_city,
                           delivery_state, delivery_zip, delivery_date, delivery_time, special_instructions):
        """Create a sales order from cart data"""
        # Use sudo for creation but ensure proper context
        # Remove website context to avoid website_id field issues when website_sale is not installed
        # Create a clean context without website_id
        clean_context = dict(request.env.context)
        clean_context.pop('website_id', None)
        sale_order_obj = request.env['sale.order'].sudo(
        ).with_context(**clean_context)
        menu_item_obj = request.env['menu.item'].sudo()

        # Prepare delivery address
        delivery_address_full = f"{delivery_address}, {delivery_city}, {delivery_state} {delivery_zip}".strip(
        )

        # Prepare delivery notes
        delivery_notes = []
        if delivery_address:
            delivery_notes.append(f"Delivery Address: {delivery_address_full}")
        if delivery_date:
            delivery_notes.append(f"Delivery Date: {delivery_date}")
        if delivery_time:
            delivery_notes.append(f"Delivery Time: {delivery_time}")
        if special_instructions:
            delivery_notes.append(
                f"Special Instructions: {special_instructions}")

        delivery_note_text = "\n".join(
            delivery_notes) if delivery_notes else "No special instructions"

        # Get company from website
        company_id = request.website.company_id.id if hasattr(
            request, 'website') and request.website else request.env.company.id

        # Get website for context
        website = request.website if hasattr(request, 'website') else False

        # Get default sales team from website or company
        team_id = False
        if website:
            # Safely try to get salesteam_id from website
            try:
                salesteam = getattr(website, 'salesteam_id', False)
                if salesteam:
                    team_id = salesteam.id
            except (AttributeError, KeyError):
                pass

        if not team_id:
            # Try to get default sales team for company
            sales_team = request.env['crm.team'].sudo().search([
                ('company_id', '=', company_id)
            ], limit=1)
            if sales_team:
                team_id = sales_team.id

        # Determine salesperson to assign (keep admin visibility)
        sales_user_id = False
        if website:
            # Safely try to get salesperson_id from website
            try:
                salesperson = getattr(website, 'salesperson_id', False)
                if salesperson:
                    sales_user_id = salesperson.id
            except (AttributeError, KeyError):
                pass

        if not sales_user_id:
            # Fallback to admin user so that orders appear in Sales by default
            try:
                sales_user_id = request.env.ref('base.user_admin').id
            except Exception:
                sales_user_id = request.env.user.id

        # Create sales order with proper context
        order_vals = {
            'partner_id': partner.id,
            'date_order': datetime.now(),
            'company_id': company_id,
            'state': 'draft',  # Explicitly set to draft
            'user_id': sales_user_id,
        }

        # Add team_id if available (makes order visible to sales team)
        if team_id:
            order_vals['team_id'] = team_id

        sale_order = sale_order_obj.create(order_vals)

        # Log order creation for debugging
        self._log_message(
            name='Menu Order Created',
            level='info',
            message=f'Sales Order created: {sale_order.name} (ID: {sale_order.id}), Partner: {partner.name}, Team: {team_id}, User: {sales_user_id}',
            func='_create_sale_order'
        )

        # Set note after creation (note might be computed from partner, so we write it explicitly)
        if delivery_note_text:
            try:
                sale_order.write({'note': delivery_note_text})
            except:
                # If note can't be written directly, append to existing note
                existing_note = sale_order.note or ''
                if existing_note:
                    sale_order.write(
                        {'note': existing_note + '\n\n' + delivery_note_text})
                else:
                    sale_order.write({'note': delivery_note_text})

        # Add order lines
        delivery_charge = 200.0  # Hardcoded delivery charge
        for item_data in cart_data:
            try:
                menu_item_id = item_data.get('id')
                quantity = float(item_data.get('quantity', 1))
                price = float(item_data.get('price', 0))

                if not menu_item_id:
                    continue

                menu_item = menu_item_obj.browse(int(menu_item_id))
                if not menu_item.exists():
                    continue

                # Create or get product for menu item
                product = self._get_or_create_product(menu_item)

                # Create order line
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'price_unit': price,
                }
                # Name will be computed from product, but we can set it explicitly
                if menu_item.name:
                    line_vals['name'] = menu_item.name

                request.env['sale.order.line'].sudo().create(line_vals)
            except Exception as e:
                # Log error but continue with other items
                self._log_message(
                    name='Menu Checkout Line Error',
                    level='error',
                    message=f'Error creating order line for item {item_data.get("id")}: {str(e)}',
                    func='_create_sale_order'
                )
                continue

        # Add delivery charge as a service product or order line
        if delivery_charge > 0:
            delivery_product = self._get_delivery_product()
            if delivery_product:
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': delivery_product.id,
                    'product_uom_qty': 1,
                    'price_unit': delivery_charge,
                    'name': 'Delivery Charge',
                }
                request.env['sale.order.line'].sudo().create(line_vals)

        # Totals are automatically computed via @api.depends when order lines are created
        # No need to manually recalculate

        return sale_order

    def _get_or_create_product(self, menu_item):
        """Get or create a product for a menu item"""
        product_obj = request.env['product.product'].sudo()

        # Check if product already exists for this menu item
        product = product_obj.search([
            ('default_code', '=', f'MENU-{menu_item.id}')
        ], limit=1)

        if product:
            # Update price if changed
            if product.list_price != menu_item.price:
                product.list_price = menu_item.price
            return product

        # Get UoM - use menu item's UoM or default to Units
        uom_id = menu_item.uom_id.id if menu_item.uom_id else False
        if not uom_id:
            uom_unit = request.env['uom.uom'].sudo().search(
                [('name', '=', 'Units')], limit=1)
            if not uom_unit:
                uom_unit = request.env['uom.uom'].sudo().search([], limit=1)
            uom_id = uom_unit.id if uom_unit else False

        # Prepare description (convert HTML to text if needed)
        description = ''
        if menu_item.short_description:
            description = menu_item.short_description
        elif menu_item.description:
            # Remove HTML tags for product description
            description = re.sub(r'<[^>]+>', '', menu_item.description)

        # Create new product
        product_vals = {
            'name': menu_item.name,
            'default_code': f'MENU-{menu_item.id}',
            'type': 'consu',  # Consumable product
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': menu_item.price or 0.0,
        }

        if uom_id:
            product_vals['uom_id'] = uom_id

        if description:
            product_vals['description'] = description

        return product_obj.create(product_vals)

    def _get_delivery_product(self):
        """Get or create delivery charge product"""
        product_obj = request.env['product.product'].sudo()

        # Look for existing delivery product
        product = product_obj.search([
            ('default_code', '=', 'DELIVERY-CHARGE')
        ], limit=1)

        if product:
            return product

        # Create delivery product
        uom_unit = request.env['uom.uom'].sudo().search(
            [('name', '=', 'Units')], limit=1)
        if not uom_unit:
            uom_unit = request.env['uom.uom'].sudo().search([], limit=1)

        product_vals = {
            'name': 'Delivery Charge',
            'default_code': 'DELIVERY-CHARGE',
            'type': 'service',
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': 200.0,
            'uom_id': uom_unit.id if uom_unit else False,
        }

        return product_obj.create(product_vals)

    @http.route('/menu/checkout/confirmation', type='http', auth='public', website=True, sitemap=False)
    def confirmation(self, **kwargs):
        """Display the order confirmation page"""
        order_data = request.session.get('order_data', {})
        if not order_data:
            # If no order data, redirect to cart
            return request.redirect('/menu/cart')

        # Ensure order_data is a dict with all required keys
        order_data = dict(order_data)  # Make a copy to ensure it's a dict

        # Set defaults for missing keys
        defaults = {
            'order_id': None,
            'order_name': 'N/A',
            'customer_name': 'N/A',
            'customer_email': 'N/A',
            'customer_phone': 'N/A',
            'delivery_address': 'N/A',
            'delivery_city': 'N/A',
            'delivery_state': 'N/A',
            'delivery_zip': 'N/A',
            'delivery_date': 'N/A',
            'delivery_time': 'N/A',
            'special_instructions': '',
            'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_amount': 0.0,
        }

        for key, default_value in defaults.items():
            if key not in order_data:
                order_data[key] = default_value

        return request.render('menu_management.checkout_confirmation', {
            'order_data': order_data,
        })

    @http.route('/menu/cart/clear', type='json', auth='public', website=True, methods=['POST'], csrf=False)
    def clear_cart(self, **kwargs):
        """Clear the cart (handled by JavaScript localStorage)"""
        return {'success': True}
