from odoo.addons.shtepsel.tests.common import TestCommon
from odoo.tests import tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'access')
class TestAccessRights(TestCommon):

    def test_carrier_user_access_rights(self):
        self.carrier = self.env['res.partner'].create({
            'name': 'Demo Carrier',
        })
        self.driver = self.env['res.partner'].create({
            'name': 'Demo Driver',
        })
        car = self.env['shtepsel.carrier'].create({
            'name': 'TE1111ST',
            'carrier_id': self.carrier.id,
            'driver_id': self.driver.id,
        })
        car.with_user(self.shtepsel_user).read()
        with self.assertRaises(AccessError):
            self.env['shtepsel.carrier'].with_user(self.shtepsel_user).create({'name': 'TE2222ST'})
        with self.assertRaises(AccessError):
            car.with_user(self.shtepsel_user).unlink()
        with self.assertRaises(AccessError):
            car.with_user(self.shtepsel_user).write({'name': 'TE3333ST'})
