from email.policy import default

from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
from odoo import fields, models,api,Command
from odoo.tools.float_utils import float_compare, float_is_zero

class Estate_Property(models.Model):
    _name = "estate.properties"
    _description = "Estate "
    _order = "name "

    name = fields.Char(required=True)
    description=fields.Text()
    active = fields.Boolean(default=True, string="Active")
    property_type = fields.Many2one(
        "estate.property.type",
        string="Property Type",required=True,
    )
    property_tags_id = fields.Many2many("estate.tags", string="Tags")
    postcode=fields.Char()
    date_availability=fields.Date(default=lambda self: fields.Date.today() + relativedelta(months=3))
    expected_price=fields.Float(required=True)

    @api.onchange('best_offer')
    def _onchange_best_offer(self):
        if self.best_offer > self.expected_price:
            self.expected_price = self.best_offer

    @api.constrains('expected_price')
    def _check_price(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError("Expected price must be greater than 0")

    selling_price = fields.Float(
        string='Selling Price',
        copy=False,
    )
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:

            # Skip if selling price is zero
            if float_is_zero(record.selling_price, precision_rounding=0.01):
                continue

            minimum_price = record.expected_price * 0.9

            if float_compare(
                    record.selling_price,
                    minimum_price,
                    precision_rounding=0.01
            ) < 0:
                raise ValidationError(
                    "The selling price cannot be lower than 90% of the expected price."
                )
    image_1920=fields.Image(string="Image")


    # Best offer price computation

    best_offer=fields.Float(string="Best Offer Price",compute="_best_offer",store="True",readonly=True)
    @api.depends("offer_id.price")
    def _best_offer(self):
        for record in self:
            if record.offer_id:
                record.best_offer = max(record.offer_id.mapped("price"))




    bedrooms=fields.Integer()

    # Total area computation
    living_area=fields.Float(string="Living Area(sqm)")
    garden_area= fields.Float(string="Garden Area(sqm)",default=10)
    Total_area=fields.Float(string="Total Area(sqm)",compute="_total_area",store=True,readonly=True)
    @api.depends("living_area","garden_area")
    def _total_area(self):
        for record in self:
            record.Total_area=record.living_area + record.garden_area
    facades=fields.Integer()
    garage=fields.Boolean()


    # Garden onchange function
    garden_orientation = fields.Selection(selection=[
        ("North", "North"), ("South", "South"), ("East", "East"), ("West", "West")
    ])
    garden=fields.Boolean(string="Garden")
    @api.onchange('garden')
    def onchange_garden(self):
        if self.garden:
            self.garden_area=45
            self.garden_orientation='North'
        else:
            self.garden_area = 0
            self.garden_orientation = False




    salesman = fields.Text()
    buyer_id = fields.Many2one("res.partner",string="Buyer")
    seller_id = fields.Many2one("res.users",string="Seller",default=lambda self: self.env.user)
    offer_id = fields.One2many(
        'property.offer',
        'property_id',
        string="Offers"
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
    )
    status=fields.Selection([("New","New"),("Offer Recieved","Offer Recieved"),("Offer Accepted","Offer Accepted"),("Sold","Sold"),("Cancelled","Cancelled")],default="New",readonly=True)



    def action_sold(self):
        for record in self:
            if record.status=="Sold":
                raise UserError("The property is already sold")
            elif record.status=="Cancelled":
                raise UserError("The property is  cancelled")
            elif record.selling_price==0:
                raise UserError("The property cannot be  sold with a selling price of 0, please accept a valid offer before selling the property.")
            else:
                record.status="Sold"
    def action_cancelled(self):
        for record in self:
            if record.status=="Sold":
                raise UserError("The property is already sold")
            elif record.status=="Cancelled":
                raise UserError("The property is  cancelled")
            else:
                record.status="Cancelled"

    # Properties can delete only when there status are new and cancelled
    @api.ondelete(at_uninstall=False)
    def _prevent_delete(self):
        for record in self:
            if record.status not in ('New', 'Cancelled'):
                raise UserError(
                    "You cannot delete a property unless its status is 'New' or 'Cancelled'."

              )

    def action_print_customer_sale_report(self):


        partner = self.buyer_id

        if not partner:
            raise UserError("No buyer found!")

        orders = self.env['sale.order'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),
        ])

        if not orders:
            raise UserError("No sale orders found!")

        total_orders = len(orders)

        total_amount = 0
        for order in orders:
            total_amount = total_amount + order.amount_total


        currency = partner.currency_id.name


        if partner.country_id:
            country = partner.country_id.name
        else:
            country = 'N/A'

        product_qty = {}
        for order in orders:
            for line in order.order_line:

                if not line.product_id:
                    continue

                product_name = line.product_id.display_name

                if product_name not in product_qty:
                    product_qty[product_name] = 0.0

                product_qty[product_name] = product_qty[product_name] + line.product_uom_qty

        sorted_products = sorted(product_qty.items(), key=lambda x: x[1], reverse=True)

        if sorted_products:
            highest = sorted_products[0][0]
            least = sorted_products[-1][0]
        else:
            highest = 'N/A'
            least = 'N/A'

        print("======= Customer Sale Report =======")
        print(f"Customer Name   : {partner.name}")
        print(f"Country         : {country}")
        print(f"Currency        : {currency}")
        print(f"Total Orders    : {total_orders}")
        print(f"Total Amount    : {total_amount}")
        print(f"Highest Product : {highest}")
        print(f"Least Product   : {least}")
        print("---- Product Wise Quantity ----")
        for product_name, qty in sorted_products:
            print(f"  {product_name} : {qty}")

    def action_create_sale_order(self):
        for record in self:

            # Step 1: Check if buyer exists
            if not record.buyer_id:
                raise UserError("No buyer found on this property!")

            # Step 2: Check if selling price exists
            if not record.selling_price:
                raise UserError("No selling price found on this property!")

            # Step 3: Find product with property name, if not found create it
            product = self.env['product.product'].search([
                ('name', '=', record.name)
            ], limit=1)

            if not product:
                product = self.env['product.product'].create({
                    'name': record.name,  # property name as product name
                    'type': 'service',
                })

            # Step 4: Create the sale order
            sale_order = self.env['sale.order'].create({
                'partner_id': record.buyer_id.id,
                'date_order': fields.Date.today(),
                'order_line': [Command.create({
                    'product_id': product.id,
                    'name': record.name,  # property name
                    'product_uom_qty': 1,
                    'price_unit': record.selling_price,  # selling price
                })],
            })

            # Step 5: Confirm → Sale Order ✅
            sale_order.action_confirm()

            # Step 6: Link sale order to this property
            record.sale_order_id = sale_order.id

            print(f"Sale Order Created : {sale_order.name}")
            print(f"Customer           : {record.buyer_id.name}")
            print(f"Property           : {record.name}")
            print(f"Selling Price      : {record.selling_price}")

