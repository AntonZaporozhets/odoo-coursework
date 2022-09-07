import logging

from math import pi, trunc, cos
from datetime import timedelta, datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ShtepselRoutePointsConstructionWizard(models.TransientModel):
    _name = 'shtepsel.route_points_construction_wizard'
    _description = 'Route points construction wizard'
    _order = 'car_number_id asc,points_sequence'

    car_number_id = fields.Many2one(
        string='Car number',
        comodel_name='shtepsel.carrier',
    )
    points_sequence = fields.Integer(
        string='Sequence of path points',
    )
    latitude = fields.Float()
    longitude = fields.Float()
    order_id = fields.Many2one(
        string='Order (begin|end points)',
        comodel_name='shtepsel.order',
    )
    order_ids = fields.Many2many(
        string='Order on segment path',
        comodel_name='shtepsel.order',
        compute='_compute_order_ids',
        store=True,
    )
    weight_segment = fields.Float(
        string='Weight on segment path',
        compute='_compute_weight_segment',
    )
    volume_segment = fields.Float(
        string='Volume on segment path',
        compute='_compute_volume_segment',
    )
    distance_segment = fields.Float(
        string='Distance between points',
        compute='_compute_distance_segment',
    )
    point_arrival_time = fields.Datetime(
        compute='_compute_point_arrival_time',
    )
    active = fields.Boolean(
        default=True,
    )

    @api.depends('car_number_id')
    def _compute_order_ids(self):
        for record in self:
            for rec in self.search([('points_sequence', '=', 0)]):
                rec.order_ids = None
            order_set = []
            for rec in self.search([('car_number_id', '=', record.car_number_id.id),
                                    ('points_sequence', '!=', 0)]). \
                    sorted(key=lambda r: r.points_sequence):
                if rec.order_id.id in order_set:
                    order_set.remove(rec.order_id.id)
                else:
                    order_set.append(rec.order_id.id)
                rec.order_ids = self.env['shtepsel.order'].browse(order_set)

    @api.depends('car_number_id')
    def _compute_weight_segment(self):
        for rec in self:
            rec.weight_segment = sum(rec.order_ids.mapped('order_weight'))

    @api.depends('car_number_id')
    def _compute_volume_segment(self):
        for rec in self:
            rec.volume_segment = sum(rec.order_ids.mapped('order_volume'))

    @api.depends('car_number_id')
    def _compute_distance_segment(self):
        for rec in self:
            recordset = self.search([('car_number_id', '=', rec.car_number_id.id)]).\
                sorted(key=lambda r: r.points_sequence)
            for i in range(len(recordset) - 1):
                recordset[i].distance_segment = self.dist(recordset[i].latitude,
                                                          recordset[i].longitude,
                                                          recordset[i + 1].latitude,
                                                          recordset[i + 1].longitude)
            recordset[-1].distance_segment = 0

    @api.depends('car_number_id')
    def _compute_point_arrival_time(self):
        for car in self.mapped('car_number_id'):
            recordset = self.search([('car_number_id', '=', car.id)]).\
                sorted(key=lambda r: r.points_sequence)
            recordset[0].point_arrival_time = datetime.now() + timedelta(hours=0.2)
            for i in range(1, len(recordset)):
                recordset[i].point_arrival_time = recordset[i - 1].point_arrival_time + \
                                timedelta(hours=(recordset[i - 1].distance_segment /
                                                 recordset[i].car_number_id.average_speed))

    def dist(self, lat1, long1, lat2, long2):
        phi1 = lat1 * pi / 180
        ly1 = long1 * pi / 180
        phi2 = lat2 * pi / 180
        ly2 = long2 * pi / 180
        return 6371.009 * ((phi2 - phi1) ** 2 + (cos((phi1 + phi2) / 2) * (ly2 - ly1)) ** 2) ** 0.5


class ShtepselRouteConstructionWizard(models.TransientModel):
    _name = 'shtepsel.route_construction_wizard'
    _description = 'Route construction wizard'

    car_id = fields.Many2one(
        string='Car (free)',
        comodel_name='shtepsel.carrier',
        domain="[('status', '=', 'free')]",
        group_expand='_expand_stages',
    )
    order_name_id = fields.Many2one(
        string='Order ID (processed)',
        comodel_name='shtepsel.order',
        domain="[('delivery_status', '=', 'processed')]",
    )
    dispatch_date = fields.Datetime(
        compute='_compute_dispatch_date',
    )
    delivery_date = fields.Datetime(
        compute='_compute_delivery_date',
    )
    dispatch_point = fields.Char(
        related='order_name_id.supplier_id.city',
    )
    delivery_point = fields.Char(
        related='order_name_id.client_id.city',
    )
    order_weight = fields.Float(
        string='Weight fullness',
        related='order_name_id.order_weight',
    )
    order_volume = fields.Float(
        string='Volume fullness',
        related='order_name_id.order_volume',
    )
    car_carrying_capacity = fields.Float(
        related='car_id.max_weight',
    )
    car_volume = fields.Float(
        related='car_id.max_volume',
    )
    efficiency = fields.Float(
        compute='_compute_efficiency',
    )

    def _expand_stages(self, states, domain, order):
        stage_ids = self.env['shtepsel.carrier'].search([('status', '=', 'free')])
        return stage_ids

    @api.depends('car_id')
    def _compute_dispatch_date(self):
        for rec in self:
            if rec.car_id.id:
                rec.dispatch_date = min(self.env['shtepsel.route_points_construction_wizard'].search([
                    ('order_id', '=', rec.order_name_id.id)]).mapped('point_arrival_time'))
            else:
                rec.dispatch_date = None

    @api.depends('car_id')
    def _compute_delivery_date(self):
        for rec in self:
            if rec.car_id.id:
                rec.delivery_date = max(self.env['shtepsel.route_points_construction_wizard'].search([
                    ('order_id', '=', rec.order_name_id.id)]).mapped('point_arrival_time'))
            else:
                rec.delivery_date = None

    @api.depends('car_id')
    def _compute_efficiency(self):
        for rec in self:
            if rec.car_id.id:
                set_loaded = self.env['shtepsel.route_points_construction_wizard'].search([
                    ('car_number_id', '=', rec.car_id.id), ('order_ids', '!=', False)]).sorted(
                    key=lambda r: r.points_sequence)
                set_not_loaded = self.env['shtepsel.route_points_construction_wizard'].search([
                    ('car_number_id', '=', rec.car_id.id), ('order_ids', '=', False)])
                dist_loaded = sum(set_loaded.mapped('distance_segment'))
                dist_not_loaded = sum(set_not_loaded.mapped('distance_segment'))
                volume_route = sum(set_loaded.mapped('order_id').mapped('order_volume'))
                weight_route = sum(set_loaded.mapped('order_id').mapped('order_weight'))
                rec.efficiency = max(volume_route / rec.car_id.max_volume, weight_route / rec.car_id.max_weight) * \
                                 dist_loaded / (dist_loaded + dist_not_loaded +
                                                self.dist(set_loaded[-1].latitude,
                                                          set_loaded[-1].longitude,
                                                          rec.car_id.carrier_id.partner_latitude,
                                                          rec.car_id.carrier_id.partner_longitude) / 5) * 100
            else:
                rec.efficiency = 0

    # the distance between two route points
    def dist(self, lat1, long1, lat2, long2):
        phi1 = lat1 * pi / 180
        ly1 = long1 * pi / 180
        phi2 = lat2 * pi / 180
        ly2 = long2 * pi / 180
        return 6371.009 * ((phi2 - phi1) ** 2 + (cos((phi1 + phi2) / 2) * (ly2 - ly1)) ** 2) ** 0.5

    # the optimal distribution of orders between carriers
    def optimal_carriers(self):
        def optimization(series_carrier):  # function for finding the optimal combination for one order
            nonlocal ef_max, series_carrier_optimal
            m = len(series_carrier)
            if m < n_carrier:
                for i in range(m + 1):
                    temp = list(series_carrier)
                    temp.insert(i, m)
                    optimization(tuple(temp))
            else:
                ef = 0
                for i in range(n_order):
                    ef += ef_delivery[i][series_carrier[i]]
                if ef > ef_max:
                    ef_max = ef
                    series_carrier_optimal = series_carrier

        # the distribution of "one order per carrier"
        lines = []
        lines_points = []
        orders = self.env['shtepsel.order'].search([('delivery_status', '=', 'processed')]).sorted(
            key=lambda r: r.order_date)
        carriers = self.env['shtepsel.carrier'].search([('status', '=', 'free')])
        n_carrier = len(carriers)
        if n_carrier:  # start point for all free carriers
            for i_ca in range(n_carrier):
                lines_points.append({
                    'car_number_id': carriers[i_ca].id,
                    'points_sequence': 0,
                    'latitude': carriers[i_ca].last_location.partner_latitude,
                    'longitude': carriers[i_ca].last_location.partner_longitude,
                })
        n_order = len(orders)
        n_order = min(n_order, n_carrier)  # the number of orders is not more than the number of carriers, others remain in the queue
        ef_delivery = []
        for i_or in range(n_order):
            ef_del_row = []
            for i_ca in range(n_carrier):
                # the distance from the supplier to the client
                dist_with_order = self.dist(orders[i_or].supplier_id.partner_latitude,
                                            orders[i_or].supplier_id.partner_longitude,
                                            orders[i_or].client_id.partner_latitude,
                                            orders[i_or].client_id.partner_longitude)
                # the distance from the current location of the carrier to the supplier +
                # the distance from the client to the carrier's garage
                dist_out_order = self.dist(carriers[i_ca].last_location.partner_latitude,
                                           carriers[i_ca].last_location.partner_longitude,
                                           orders[i_or].supplier_id.partner_latitude,
                                           orders[i_or].supplier_id.partner_longitude) + \
                                 self.dist(orders[i_or].client_id.partner_latitude,
                                           orders[i_or].client_id.partner_longitude,
                                           carriers[i_ca].carrier_id.partner_latitude,
                                           carriers[i_ca].carrier_id.partner_longitude) / 5
                # the efficiency of "one order per carrier"
                ef_del_row.append(max(orders[i_or].order_volume / carriers[i_ca].max_volume,
                                      orders[i_or].order_weight / carriers[i_ca].max_weight) *
                                  dist_with_order / (dist_with_order + dist_out_order) *
                                  (1 if trunc(carriers[i_ca].max_weight / orders[i_or].order_weight) *
                                        trunc(carriers[i_ca].max_volume / orders[i_or].order_volume) *
                                        trunc(carriers[i_ca].max_height / orders[i_or].order_max_height) *
                                        trunc(
                                            carriers[i_ca].max_length / orders[i_or].order_max_length) != 0 else -1000))
            ef_delivery.append(ef_del_row)
        series_carrier_optimal = ()
        ef_max = -1000
        optimization((0,))
        carrier_number = series_carrier_optimal[0:n_order]

        if not carrier_number:
            if len(orders) == 0:
                raise ValidationError(_(f'No routes have been built. There are no orders'))
            if len(carriers) == 0:
                raise ValidationError(_(f'No routes have been built. There are no free carriers'))
        else:
            for i_or in range(n_order):
                # two points of the route of one order (loading at the supplier, unloading at the client)
                lines_points.append({
                    'car_number_id': carriers[carrier_number[i_or]].id,
                    'points_sequence': 1000,
                    'latitude': orders[i_or].supplier_id.partner_latitude,
                    'longitude': orders[i_or].supplier_id.partner_longitude,
                    'order_id': orders[i_or].id,
                })
                lines_points.append({
                    'car_number_id': carriers[carrier_number[i_or]].id,
                    'points_sequence': 2000,
                    'latitude': orders[i_or].client_id.partner_latitude,
                    'longitude': orders[i_or].client_id.partner_longitude,
                    'order_id': orders[i_or].id,
                })
                # record of the route
                lines.append({
                    'car_id': carriers[carrier_number[i_or]].id,
                    'order_name_id': orders[i_or].id,
                })
            # undistributed orders
            if len(orders) > n_carrier:
                for i_or in range(n_carrier, len(orders)):
                    lines.append({
                        'order_name_id': orders[i_or].id,
                    })
            self.search([]).unlink()
            self.env['shtepsel.route_points_construction_wizard'].search([]).unlink()
            self.create(lines)
            self.env['shtepsel.route_points_construction_wizard'].create(lines_points)

            return {
                'name': _('Route construction'),
                'type': 'ir.actions.act_window',
                'view_mode': 'kanban',
                'view_id': self.env.ref('shtepsel.shtepsel_route_construction_wizard_kanban').id,
                'res_model': 'shtepsel.route_construction_wizard',
                'target': 'current',
            }

    @api.onchange('car_id')
    def _onchange_car_id(self):
        route_old = self.env['shtepsel.route_points_construction_wizard'].search(
            [('order_id', '=', self.order_name_id.id)]).sorted(key=lambda r: r.points_sequence)
        for rec in route_old:
            rec.active = False
        start_latitude = self.order_name_id.supplier_id.partner_latitude
        start_longitude = self.order_name_id.supplier_id.partner_longitude
        finish_latitude = self.order_name_id.client_id.partner_latitude
        finish_longitude = self.order_name_id.client_id.partner_longitude
        if self.car_id.id:
            if self.order_name_id.order_max_height > self.car_id.max_height or \
                    self.order_name_id.order_max_length > self.car_id.max_length:
                raise ValidationError(
                    _(f'The dimensions of the product exceed the permissible dimensions for this car'))
            route_new = self.env['shtepsel.route_points_construction_wizard'].search(
                [('car_number_id', '=', self.car_id.id)]).sorted(key=lambda r: r.points_sequence)
            # the distribution optimization of "some order per carrier"
            if len(route_new) > 1:
                d = 1e10
                i_start = 0
                d2 = self.dist(route_new[0].latitude, route_new[0].longitude, start_latitude, start_longitude)
                for i in range(len(route_new) - 1):
                    d1 = d2
                    d2 = self.dist(start_latitude, start_longitude,
                                   route_new[i + 1].latitude, route_new[i + 1].longitude)
                    if d1 + d2 - route_new[i].distance_segment < d:
                        d = d1 + d2 - route_new[i].distance_segment
                        i_start = i
                        # if i_start is before the last point of the new route
                if i_start < len(route_new) - 2 or route_new[i_start].distance_segment + d2 - d1 > d:
                    points_sequence_1 = (route_new[i_start].points_sequence +
                                         route_new[i_start + 1].points_sequence) / 2 - 50
                else:
                    points_sequence_1 = route_new[-1].points_sequence + 1000
                    i_start += 1
                    route_new_correct = 0
                d = 1e10  # if i_finish is before the last point of the new route
                i_finish = i_start
                d2 = self.dist(start_latitude, start_longitude,#route_new[i_start].latitude, route_new[i_start].longitude,
                               finish_latitude, finish_longitude)
                for i in range(i_start, len(route_new) - 1):
                    d1 = d2
                    d2 = self.dist(finish_latitude, finish_longitude,
                                   route_new[i + 1].latitude, route_new[i + 1].longitude)
                    if i == i_start:
                        route_new_correct = self.dist(start_latitude, start_longitude,
                                                      route_new[i + 1].latitude, route_new[i + 1].longitude)
                    else:
                        route_new_correct = route_new[i].distance_segment
                    if d1 + d2 - route_new_correct < d:
                        d = d1 + d2 - route_new_correct
                        i_finish = i
                if i_finish < len(route_new) - 2 or route_new_correct + d2 - d1 > d:
                    points_sequence_2 = (route_new[i_finish].points_sequence +
                                         route_new[i_finish + 1].points_sequence) / 2 + 50
                else:
                    points_sequence_2 = points_sequence_1 + 1000
                if self.order_name_id.order_volume + route_new[i_start].volume_segment > self.car_id.max_volume:
                    raise ValidationError(_(f'The volume of the product exceeds the permissible volume for this car'))
                if self.order_name_id.order_weight + route_new[i_start].weight_segment > self.car_id.max_weight:
                    raise ValidationError(_(f'The weight of the product exceeds the permissible weight for this car'))
            else:
                if self.order_name_id.order_volume > self.car_id.max_volume:
                    raise ValidationError(_(f'The volume of the product exceeds the permissible volume for this car'))
                if self.order_name_id.order_weight > self.car_id.max_weight:
                    raise ValidationError(_(f'The weight of the product exceeds the permissible weight for this car'))
                points_sequence_1 = 1000
                points_sequence_2 = 2000
            lines_points = []
            lines_points.append({
                'car_number_id': self.car_id.id,
                'points_sequence': points_sequence_1,
                'latitude': start_latitude,
                'longitude': start_longitude,
                'order_id': self.order_name_id.id,
            })
            lines_points.append({
                'car_number_id': self.car_id.id,
                'points_sequence': points_sequence_2,
                'latitude': finish_latitude,
                'longitude': finish_longitude,
                'order_id': self.order_name_id.id,
            })
            self.env['shtepsel.route_points_construction_wizard'].create(lines_points)

    def refresh_constructor(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def route_create(self):
        order_list = [False]
        car = ''
        for rec in self.env['shtepsel.route_points_construction_wizard'].search([]):
            if len(self.env['shtepsel.route_points_construction_wizard'].search([
                    ('car_number_id', '=', rec.car_number_id.id)])) > 1:
                if rec.car_number_id.name != car:
                    code = self.env["ir.sequence"].next_by_code("shtepsel.route")
                    car = rec.car_number_id.name
                    values = {
                        'route_number': f'{rec.car_number_id.name} - {code}',
                        'car_id': rec.car_number_id.id,
                        'waybill_order_ids': self.env['shtepsel.route_points_construction_wizard'].search([
                            ('car_number_id', '=', rec.car_number_id.id)]).mapped('order_id.id')
                    }
                    self.env['shtepsel.waybill'].create(values)
                if rec.order_id.id not in order_list:
                    loading_status = 'loading'
                    order_list.append(rec.order_id.id)
                    point = f'{rec.order_id.supplier_id.city}'
                elif not rec.order_id.id:
                    loading_status = ''
                    point = f'{rec.car_number_id.carrier_id.city}'
                else:
                    loading_status = 'unloading'
                    point = f'{rec.order_id.client_id.city}'
                values = {
                    'route_number_id': self.env['shtepsel.waybill'].search([
                            ('waybill_order_ids', 'in', self.env['shtepsel.route_points_construction_wizard'].search([
                            ('car_number_id', '=', rec.car_number_id.id)]).mapped('order_id.id'))]).id,
                    'carrier_id': rec.car_number_id.carrier_id.id,
                    'car_id': rec.car_number_id.id,
                    'order_ids': rec.order_ids,
                    'weight_segment': rec.weight_segment,
                    'volume_segment': rec.volume_segment,
                    'point_arrival_time': rec.point_arrival_time,
                    'distance_segment': rec.distance_segment,
                    'order_id': rec.order_id.id,
                    'point': point,
                    'loading_status': loading_status,
                    'efficiency': self.search([('order_name_id', '=', rec.order_id.id)]).efficiency,
                }
                self.env['shtepsel.route'].create(values)
        for rec in self.env['shtepsel.route_points_construction_wizard'].search([]).mapped('order_id'):
            rec.write({'delivery_status': 'sent'})
        for rec in self.env['shtepsel.route_points_construction_wizard'].search([
                ('order_id', '!=', False)]).mapped('car_number_id'):
            rec.write({'status': 'on_the_way'})
        return {
            'name': _('Routes'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'shtepsel.route',
            'target': 'main',
            'context': {'search_default_group_by_route_number': 1},
        }
