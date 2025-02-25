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

    expense_entries_count = fields.Integer(string="Expense Entries", compute="_compute_expense_entries_count")



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


# report
    def action_fleet_income_expense_report(self):
        expenses = self.env['account.move'].search([
            ('vehicle_id', '=', self.id),
            ('move_type', '=', 'in_invoice'),
        ])

        income = self.env['account.move'].search([
            ('vehicle_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
        ])
        expense_details = []
        for expense in expenses:
            expense_details.append({
                'bill_id': expense.name,
                'amount': expense.amount_total,
                'date': expense.date,
                # 'partner_name': expense.partner_id.name,
            })

        income_details = []
        for invoice in income:
            income_details.append({
                'invoice_id': invoice.name,
                'amount': invoice.amount_total,
                'date': invoice.date,
                # 'partner_name': invoice.partner_id.name,
            })

        # Prepare the report data
        report_data = {
            'vehicle': self,
            'vehicle_name': self.name,
            'expenses': expense_details,
            'income': income_details,
        }
        return self.env.ref('fleet_management.fleet_income_expense_report_action').report_action(self, data=report_data)


# fleet maintenance history report

    def action_fleet_maintenance_history_report(self):
        maintenance_records = self.env['fleet.vehicle.log.services'].search([
            ('vehicle_id', '=', self.id)
        ])

        maintenance_details = []
        for record in maintenance_records:
            maintenance_details.append({
                # 'service_id': record.reference or 'N/A',  # Reference instead of 'name'
                'date': record.date or 'N/A',
                'description': record.description or 'N/A',
                'service_type': record.service_type_id.name if record.service_type_id else 'N/A',
                'vehicle': record.vehicle_id.name if record.vehicle_id else 'N/A',
                'driver': record.purchaser_id.name if record.purchaser_id else 'N/A',
                'vendor': record.vendor_id.name if record.vendor_id else 'N/A',
                # 'notes': record.notes or 'N/A',
                'cost': record.amount or 0.0,
                # 'state': record.state.id if record.state.id else 'N/A',
            })

        report_data = {
            'vehicle_name': self.name,
            'license_plate': self.license_plate,
            'maintenance_records': maintenance_details,
        }

        return self.env.ref('fleet_management.fleet_maintenance_history_report_action').report_action(self,data=report_data)
