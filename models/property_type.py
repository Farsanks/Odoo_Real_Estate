

from odoo import fields,models,api
from odoo.exceptions import ValidationError

class PropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'The Type of the property can be defined here'
    _order = 'name'

    name = fields.Char(required=True)
    property_type = fields.Many2one('estate.property.type', string="Property Type")
    sequence=fields.Integer(default=1)
    property_id = fields.One2many(
        "estate.properties",
        "property_type",
        string="Properties"
    )
    offer_id = fields.One2many(
        'property.offer',
        'property_type_id',
        string="Offers"

    )

    offer_count = fields.Integer(
        string="Offer Count",
        compute="_compute_offer_count"
    )

    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.mapped('property_id.offer_id'))

    def offer_count_action(self):
        return {
            'name': 'Offers',
            'type': 'ir.actions.act_window',
            'res_model': 'property.offer',
            'view_mode': 'list,form',
            'domain': [('property_id.property_type', '=', self.id)],
        }
    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if self.search_count([('name', '=ilike', rec.name)]) > 1:
                raise ValidationError("Property type  must be unique!")
class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Property"

    name = fields.Char()

    property_type = fields.Many2one(
        "estate.property.type",
        string="Property Type"
    )