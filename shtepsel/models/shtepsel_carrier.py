import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ShtepselCarrier(models.Model):
    _name = 'shtepsel.carrier'
    _description = 'Shtepsel carrier'

    name = fields.Char(
        string='Car number',
    )
    carrier_id = fields.Many2one(
        comodel_name='res.partner',
        domain='[("partner_group_id.id", "=", 2)]',
    )
    driver_id = fields.Many2one(
        comodel_name='res.partner',
        domain='[("partner_group_id.id", "=", 3)]',
    )
    max_weight = fields.Float()
    max_volume = fields.Float()
    max_height = fields.Float()
    max_length = fields.Float()
    average_speed = fields.Float()
    last_location = fields.Many2one(
        comodel_name='res.partner',
    )
    act_location = fields.Char(
        string='Actual location',
        related='last_location.city',
    )
    status = fields.Selection(
        selection=[('free', 'Free'),
                   ('on_the_way', 'On the way'),
                   ('inactive', 'Inactive')],
        default='inactive',
    )
    active = fields.Boolean(
        default=True,
    )

    def to_garage(self):
        self.last_location = self.carrier_id.id
