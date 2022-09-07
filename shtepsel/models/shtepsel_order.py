import logging
from math import cos, pi
from datetime import timedelta, datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ShtepselOrder(models.Model):
    _name = 'shtepsel.order'
    _description = 'Shtepsel order'

    name = fields.Char(
        string='Order №',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
    )
    order_date = fields.Date(
        default=fields.Datetime.now(),
        readonly=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        domain='[("partner_group_id.id", "=", 4)]',
    )
    client_city = fields.Char(
        string='',
        related='client_id.city',
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        domain='[("partner_group_id.id", "=", 1)]',
    )
    supplier_city = fields.Char(
        string=' ',
        related='supplier_id.city'
    )
    order_cost = fields.Float(
        string='Total cost',
        compute='_compute_cost',
    )
    order_weight = fields.Float(
        string='Total weight',
        compute='_compute_weight',
    )
    order_volume = fields.Float(
        string='Total volume',
        compute='_compute_volume',
    )
    order_max_length = fields.Float(
        string='Max length',
        compute='_compute_max_length',
    )
    order_max_height = fields.Float(
        string='Max height',
        compute='_compute_max_height',
    )
    distance = fields.Float(
        compute='_compute_distance',
    )
    delivery_cost = fields.Float(
        compute='_compute_delivery_cost',
    )
    delivery_date = fields.Datetime(
        compute='_compute_delivery_date',
    )
    delivery_status = fields.Selection(
        selection=[('processed', 'Processed'),
                   ('sent', 'Sent'),
                   ('delivered', 'Delivered')],
        default='processed',
    )
    order_line_ids = fields.One2many(
        comodel_name='shtepsel.order_line',
        inverse_name='order_id',
        string='Order Lines',
        copy=True,
        auto_join=True
    )
    active = fields.Boolean(
        default=True,
    )

    @api.depends("order_line_ids")
    def _compute_cost(self):
        for rec in self:
            rec.order_cost = sum(line.cost for line in rec.order_line_ids)

    @api.depends("order_line_ids")
    def _compute_weight(self):
        for rec in self:
            rec.order_weight = sum(line.count * line.product_id.weight for line in rec.order_line_ids)

    @api.depends("order_line_ids")
    def _compute_volume(self):
        for rec in self:
            rec.order_volume = sum(line.count * line.product_id.length * line.product_id.width * line.product_id.height
                                   for line in rec.order_line_ids)

    @api.depends("order_line_ids")
    def _compute_max_height(self):
        for rec in self:
            rec.order_max_height = max(line.product_id.height for line in rec.order_line_ids)

    @api.depends("order_line_ids")
    def _compute_max_length(self):
        for rec in self:
            rec.order_max_length = max(max(line.product_id.length,line.product_id.width) for line in rec.order_line_ids)

    @api.depends("client_id", "supplier_id")
    def _compute_distance(self):
        for rec in self:
            if rec.client_id.partner_latitude * rec.client_id.partner_longitude == 0:
                rec.client_id.geo_localize()
            if rec.supplier_id.partner_latitude * rec.supplier_id.partner_longitude == 0:
                rec.supplier_id.geo_localize()
            phi1 = rec.client_id.partner_latitude * pi/180
            ly1 = rec.client_id.partner_longitude * pi/180
            phi2 =rec.supplier_id.partner_latitude * pi/180
            ly2 = rec.supplier_id.partner_longitude * pi/180
            rec.distance = 6371.009 * ((phi2 - phi1)**2+(cos((phi1 + phi2)/2) * (ly2 - ly1))**2)**0.5

    @api.depends("distance")
    def _compute_delivery_cost(self):
        for rec in self:
            rec.delivery_cost = rec.distance / 100 * max(rec.order_weight / 100, rec.order_volume / 10) * 10

    @api.depends("distance")
    def _compute_delivery_date(self):
        for rec in self:
            rec.delivery_date = datetime.now() + timedelta(hours=(rec.distance / 80 + 24))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'shtepsel.order') or _('New')
        res = super().create(vals)
        return res
