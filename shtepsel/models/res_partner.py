import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_group_id = fields.Many2one(
        comodel_name='shtepsel.partner_group',
        index=True,
    )
