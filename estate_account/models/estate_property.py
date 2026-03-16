from odoo import models, fields, Command


class EstateProperty(models.Model):
    # inherit the existing estate.property model
    # we are NOT creating a new model
    # we are EXTENDING the existing one
    _inherit = 'estate.properties'

    def action_sold(self):
        for record in self:
            self.env['account.move'].create({
                'move_type': 'out_invoice', 'partner_id': record.buyer_id.id, 'invoice_date': fields.Date.today(),
                'invoice_line_ids': [Command.create({
                    'name': record.name,
                    'quantity': 1,
                    'price_unit': record.selling_price,
                }),
                    Command.create({
                        'name': 'Administrative Fees',
                        'quantity': 1,
                        'price_unit': 100.00,
                    }),
                ],
            })
        return super().action_sold()
