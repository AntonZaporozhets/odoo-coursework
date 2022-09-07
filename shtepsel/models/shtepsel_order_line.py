import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ShtepselOrderLine(models.Model):
    _name = 'shtepsel.order_line'
    _description = 'Shtepsel order line'
    _order = 'order_id, id'

    order_id = fields.Many2one(
        string='Order Reference',
        comodel_name='shtepsel.order',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
    )
    price = fields.Float(
        related='product_id.list_price',
    )
    count = fields.Float()
    cost = fields.Float(
        compute='_compute_cost',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if self.product_id.list_price == 0:
                raise ValidationError(_(f'Please check the price of the product'))
            if self.product_id.weight == 0:
                raise ValidationError(_(f'Please check the weight of the product'))
            if self.product_id.length == 0:
                raise ValidationError(_(f'Please check the length of the product'))
            if self.product_id.width == 0:
                raise ValidationError(_(f'Please check the width of the product'))
            if self.product_id.height == 0:
                raise ValidationError(_(f'Please check the height of the product'))

    @api.depends('count')
    def _compute_cost(self):
        for rec in self:
            rec.cost = rec.count * rec.product_id.list_price
