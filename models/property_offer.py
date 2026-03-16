from datetime import timedelta
from odoo import fields,models,api
from odoo.exceptions import UserError,ValidationError


class Property_Offer(models.Model):
    _name = "property.offer"
    _description = "Property Offer"
    _order = "price desc"



    # Offer price must be greater than 0
    price = fields.Float(string="Price")
    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price<=0:
                raise ValidationError("Offer price must be greater than 0")



    status = fields.Selection([('Accepted', 'Accepted'),
            ('Refused', 'Refused')])
    partner_id = fields.Many2one("res.partner",string="Buyer",required=True)
    property_id = fields.Many2one("estate.properties",string="Property",required=True,readonly=True,ondelete="cascade",)
    property_type_id = fields.Many2one(
        "estate.properties",
        store=True,
        string="Property Type"
    )


    # deadline computation and inverse function for updating computed feild
    validity=fields.Integer(default=7,required=False)
    deadline=fields.Date(compute="_compute_deadline",store="True",inverse="_inverse_deadline")
    @api.depends('validity')
    def _compute_deadline(self):
        for record in self:
            record.deadline=fields.Date.today()+timedelta(days=record.validity)
    def _inverse_deadline(self):
        for record in self:
            record.deadline=record.deadline-timedelta(days=record.validity)




    # Offer Accepted and Refused Button action methods

    def action_confirm(self):
        for record in self:

            accepted_offer = self.search([
                ('property_id', '=', record.property_id.id),
                ('status', '=', 'Accepted')
            ])

            if accepted_offer:
                raise UserError("An offer has already been accepted for this property.")

            record.status = "Accepted"
            record.property_id.buyer_id=record.partner_id
            record.property_id.selling_price=record.price
            record.property_id.status='Offer Accepted'



    def action_cancel(self):
        for record in self:
            record.status = "Refused"


    #         Status changes from New to Offer Received

    @api.constrains('property_id')
    def _check_property_offer(self):
        for record in self:
            if record.property_id and record.property_id.status not in ['Sold', 'Cancelled','Offer Accepted']:
                record.property_id.status = "Offer Recieved"


    # Offers cannot be created for cancelled and sold propertiies

    @api.constrains('property_id')
    def _check_property_sold(self):
        for record in self:
            if record.property_id.status in ['Sold','Offer Accepted','Cancelled']:
                raise ValidationError("No offers can be created for properties that are either sold,cancelled or accepted")

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            property_record = self.env['estate.properties'].browse(vals['property_id'])

            # Find highest existing offer
            existing_offers = self.search([
                ('property_id', '=', property_record.id)
            ])

            if existing_offers:
                highest_offer = max(existing_offers.mapped('price'))

                if vals['price'] < highest_offer:
                    raise ValidationError(
                        "You cannot create an offer lower than an existing offer."
                    )

            # Change property status
            if property_record.status == 'New':
                property_record.status = 'Offer Recieved'

        return super().create(vals_list)