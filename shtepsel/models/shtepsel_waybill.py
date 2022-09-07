import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ShtepselWaybill(models.Model):
    _name = 'shtepsel.waybill'
    _description = 'Shtepsel waybill'
    _rec_name = 'route_number'

    route_number = fields.Char(
        string='Route №',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
    )
    waybill_order_ids = fields.Many2many(
        comodel_name='shtepsel.order',
    )
    car_id = fields.Many2one(
        string='Car number',
        comodel_name='shtepsel.carrier',
        readonly=True,
    )
    carrier_id = fields.Many2one(
        related='car_id.carrier_id',
        store=True,
    )
    driver_id = fields.Many2one(
        related='car_id.driver_id',
        store=True,
    )
    weight_fullness = fields.Float(
        compute='_compute_weight',
    )
    volume_fullness = fields.Float(
        compute='_compute_volume',
    )
    car_carrying_capacity = fields.Float(
        related='car_id.max_weight',
    )
    car_volume = fields.Float(
        related='car_id.max_volume',
    )
    route_duration = fields.Float(
        compute='_compute_duration',
        store=True,
    )
    finish_time_point = fields.Datetime(
        compute='_compute_finish_time',
        store=True,
    )
    route_number_ids = fields.One2many(
        comodel_name='shtepsel.route',
        inverse_name='route_number_id',
        string='Route points',
        copy=True,
        auto_join=True
    )
    active = fields.Boolean(
        default=True,
    )

    @api.depends("route_number_ids")
    def _compute_weight(self):
        for rec in self:
            rec.weight_fullness = max(line.weight_segment for line in rec.route_number_ids)

    @api.depends("route_number_ids")
    def _compute_volume(self):
        for rec in self:
            rec.volume_fullness = max(line.volume_segment for line in rec.route_number_ids)

    @api.depends("route_number_ids")
    def _compute_duration(self):
        for rec in self:
            rec.route_duration = (rec.route_number_ids[-1].point_arrival_time-rec.route_number_ids[0].point_arrival_time).seconds/3600

    @api.depends("route_number_ids")
    def _compute_finish_time(self):
        for rec in self:
            rec.finish_time_point = rec.route_number_ids[-1].point_arrival_time

    def write(self, vals):
        rec = super().write(vals)
        route_set = self.env['shtepsel.route'].search([('route_number_id', '=', self.route_number)])
        if route_set[-1].delivery_confirm:
            self.env['shtepsel.carrier'].search([
                ('carrier_id', '=', self.carrier_id.id)]).write({'status': 'free',
                                                                 'last_location': route_set[-1].order_id.client_id.id})
        for order in route_set.mapped('order_id'):
            if len(route_set.search([('order_id', '=', order.id), ('delivery_confirm', '=', True)])) == 2:
                self.env['shtepsel.order'].search([('id', '=', order.id)]).write({'delivery_status': 'delivered'})
        return rec
