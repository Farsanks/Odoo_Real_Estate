from odoo import fields, models

class UserInheritedModel(models.Model):
    _inherit = "res.users"

    property_ids= fields.One2many("estate.properties","seller_id",domain=[('status', '=', 'New')])

