
from odoo import fields,models,api
from odoo.exceptions import ValidationError

class PropertyTags(models.Model):
    _name = 'estate.tags'
    _description = "Estate Property Tags"
    _order = "name"


    name = fields.Char(required=True)
    color = fields.Integer(string="Color")

    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if self.search_count([('name', '=ilike', rec.name)]) > 1:
                raise ValidationError("Tag name must be unique!")

