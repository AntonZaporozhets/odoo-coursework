from math import cos, pi
from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):

    def setUp(self):
        super(TestCommon, self).setUp()
        self.group_shtepsel_user = self.env.ref('shtepsel.group_shtepsel_user')
        self.group_shtepsel_admin = self.env.ref('shtepsel.group_shtepsel_admin')
        self.shtepsel_user = self.env['res.users'].create({
            'name': 'Driver',
            'login': 'shtepsel_user',
            'groups_id': [(4, self.env.ref('base.group_user').id),
                          (4, self.group_shtepsel_user.id)],
        })
        self.shtepsel_admin = self.env['res.users'].create({
            'name': 'Admin',
            'login': 'shtepsel_admin',
            'groups_id': [(4, self.env.ref('base.group_user').id),
                          (4, self.group_shtepsel_admin.id)],
        })

    def test_partner_group(self):
        self.partner_group_demo = self.env['shtepsel.partner_group'].create({'group': 'staff'})
        self.assertTrue(self.partner_group_demo.id > 4)

    def test_order(self):
        self.client = self.env['res.partner'].create({
            'name': 'Demo Client',
            'partner_latitude': 53,
            'partner_longitude': 27,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Demo Supplier',
            'partner_latitude': 41,
            'partner_longitude': 57,
        })
        self.order = self.env['shtepsel.order'].create({
            'client_id': self.client.id,
            'supplier_id': self.supplier.id,
        })
        phi1 = 53 * pi / 180
        ly1 = 27 * pi / 180
        phi2 = 41 * pi / 180
        ly2 = 57 * pi / 180
        temp = 6371.009 * ((phi2 - phi1) ** 2 + (cos((phi1 + phi2) / 2) * (ly2 - ly1)) ** 2) ** 0.5
        self.assertTrue(abs(self.order.distance - temp) < 100)

        self.assertEqual(self.order.delivery_status, 'processed')

        self.assertFalse(self.order.order_line_ids)
