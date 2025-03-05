from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_vendor = fields.Boolean(string="Is Vendor")

    employee_fines_count = fields.Integer(compute='_compute_employee_fines_count', string="Employee Fines")

    fine_count = fields.Integer(string="Fine Count", compute="_compute_fine_count")

    def _compute_fine_count(self):
        for partner in self:
            partner.fine_count = self.env['fleet.driver.fine'].search_count([('partner_id', '=', partner.id)])

    def button_view_driver_fines(self):
        return {
            'name': 'Driver Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.driver.fine',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('partner_id', '=', self.id)],
        }





