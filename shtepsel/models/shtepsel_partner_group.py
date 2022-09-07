import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ShtepselPartnerGroup(models.Model):
    _name = 'shtepsel.partner_group'
    _description = 'Shtepsel partner group'
    _rec_name = 'group'
    _order = 'id'

    group = fields.Char(
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )
