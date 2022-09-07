import logging

from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ShtepselRoute(models.Model):
    _name = 'shtepsel.route'
    _description = 'Shtepsel routes'

    route_number_id = fields.Many2one(
        string='Route №',
        comodel_name='shtepsel.waybill',
    )
    carrier_id = fields.Many2one(
        comodel_name='res.partner',
        readonly=True,
    )
    car_id = fields.Many2one(
        string='Car number',
        comodel_name='shtepsel.carrier',
    )
    order_ids = fields.Many2many(
        string='Orders',
        comodel_name='shtepsel.order',
        readonly=True,
    )
    weight_segment = fields.Float(
        string='Weight on segment path',
        readonly=True,
    )
    volume_segment = fields.Float(
        string='Volume on segment path',
        readonly=True,
    )
    point_arrival_time = fields.Datetime(
        readonly=True,
    )
    distance_segment = fields.Float(
        string='Distance between points',
        readonly=True,
    )
    order_id = fields.Many2one(
        comodel_name='shtepsel.order',
        readonly=True,
    )
    point = fields.Char(
        readonly=True,
    )
    loading_status = fields.Char(
        string='Loading / unloading',
        readonly=True,
    )
    is_delayed = fields.Boolean(
        compute='_compute_delayed',
    )
    efficiency = fields.Float(
        readonly=True,
        group_operator='max',
    )
    delivery_confirm = fields.Boolean(
        string='Delivery confirmation',
    )
    active = fields.Boolean(
        default=True,
    )

    @api.depends("point_arrival_time")
    def _compute_delayed(self):
        for rec in self:
            rec.is_delayed = bool(rec.point_arrival_time < datetime.now() and not rec.delivery_confirm)
