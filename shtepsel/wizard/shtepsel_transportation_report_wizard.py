import logging

from datetime import datetime
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ShtepselTransportationReportWizard(models.TransientModel):
    _name = 'shtepsel.transportation_report_wizard'
    _description = 'Transportation report wizard'

    start_date = fields.Date()
    end_date = fields.Date()

    def action_print_transportation_report(self):

        records = self.env['shtepsel.route'].search([('point_arrival_time', '>', datetime.combine(self.start_date, datetime.min.time())),
                                                     ('point_arrival_time', '<', datetime.combine(self.end_date, datetime.max.time()))])

        list_report = []
        for rec_carrier in records.mapped('carrier_id'):
            list_carrier = []
            car_records = records.search([('carrier_id', '=', rec_carrier.id)])
            for rec_car in car_records.mapped('car_id'):
                list_car = []
                for rec in car_records.search([('car_id', '=', rec_car.id), ('loading_status', '=', 'loading')]):
                    list_car.append(
                        {
                            'supplier': rec.order_id.supplier_id.name,
                            'client': rec.order_id.client_id.name,
                            'efficiency': f'{round(rec.efficiency,2)} %',
                        }
                    )
                list_carrier.append(
                    {
                        'car': rec_car.name,
                        'data_car': list_car,
                    }
                )
            list_report.append(
                {
                    'carrier': rec_carrier.name,
                    'data_carrier': list_carrier,
                }
            )
        return self.env.ref('shtepsel.action_report_transportation').report_action(self, data={'data': list_report})
