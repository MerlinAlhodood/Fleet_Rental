from odoo import models, fields



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_driver = fields.Boolean(string="Is Driver", default=False)
