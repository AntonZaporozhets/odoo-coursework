import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
