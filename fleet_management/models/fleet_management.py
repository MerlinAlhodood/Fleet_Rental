from odoo import models, fields, api
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", readonly=True)


# smart button for fleet

    def action_expense_entries(self):
        bills = self.env['account.move'].search([
            ('vehicle_id', '=', self.id),
            ('move_type', '=', 'in_invoice'),
        ])
        print(bills,'bilssss')

        return {
            'name': 'Expense Entries',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', bills.ids)],
            'context': {'default_vehicle_id': self.id},
        }

    def _compute_expense_entries_count(self):

        for record in self:
            record.expense_entries_count = self.env['account.move'].search_count([
                ('vehicle_id', '=', record.id),
                ('move_type', '=', 'in_invoice'),
            ])

    expense_entries_count = fields.Integer(string="Expense Entries Count", compute="_compute_expense_entries_count")









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

