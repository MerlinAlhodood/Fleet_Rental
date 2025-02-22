from odoo import models, fields, api
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", readonly=True)

    @api.model
    def create(self, vals):

        default_plan = self.env['account.analytic.plan'].search([], limit=1)

        # 'plan_id': self.env.ref('analytic.analytic_plan_projects').id,

        if not default_plan:
            raise UserError("No analytic plan found. Please configure an analytic plan.")


        analytic_account_vals = {
            'name': vals.get('license_plate', 'New Vehicle') + ' Account',
            'company_id': vals.get('company_id'),
            'plan_id': default_plan.id,
        }

        analytic_account = self.env['account.analytic.account'].create(analytic_account_vals)


        vals['analytic_account_id'] = analytic_account.id
        return super(FleetVehicle, self).create(vals)