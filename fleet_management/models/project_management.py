from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    rent_types = fields.Selection(
        [ ('weekly', 'Weekly'),('monthly', 'Monthly'),('yearly', 'Yearly')],
        string="Rent Type",
        default='weekly',
    )
    rent_amount = fields.Float(string="Rent Amount")

    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        'project_vehicle_rel',
        'project_id',
        'vehicle_id',
        string="Vehicles"
    )

    expense_entry_ids = fields.One2many('project.expense.entry', 'project_id', string="Expense Entries")
    contract_line_ids = fields.One2many('project.contract.line', 'project_id', string="Invoice Entries")


    def action_schedule(self):

        self.ensure_one()

        # Check if the required fields are filled
        if not self.rent_amount or not self.date_start or not self.date:
            raise ValueError("Please provide Rent Amount, Start Date, and End Date.")

        # Generate rent lines based on the rent type
        if self.rent_types == 'weekly':
            self._generate_weekly_rent_lines()
        elif self.rent_types == 'monthly':
            self._generate_monthly_rent_lines()
        elif self.rent_types == 'yearly':
            self._generate_yearly_rent_lines()

    def _generate_weekly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date)

        while current_date < end_date:  # We exclude the end date
            self.env['project.contract.line'].create({
                'project_id': self.id,
                'date': current_date,
                'amount': self.rent_amount,
            })

            # Move to the next week
            current_date += timedelta(weeks=1)

    def _generate_monthly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date)

        while current_date < end_date:  # We exclude the end date
            # Create the contract line with the full rent amount (no proration)
            self.env['project.contract.line'].create({
                'project_id': self.id,
                'date': current_date,
                'amount': self.rent_amount,
            })

            # Move to the next month
            current_date = current_date.replace(
                year=current_date.year + (current_date.month // 12),
                month=((current_date.month) % 12) + 1,
                day=1
            )

    def _generate_yearly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date)

        while current_date < end_date:
            self.env['project.contract.line'].create({
                'project_id': self.id,
                'date': current_date,
                'amount': self.rent_amount,
            })

            current_date = current_date.replace(year=current_date.year + 1)






class ProjectExpenseEntry(models.Model):
    _name = 'project.expense.entry'
    _description = 'Expense Entry for Project'

    bill_id = fields.Many2one(
        'account.move',
        string="Vendor Bill",
        domain="[('move_type', '=', 'in_invoice'), ('type_selection', '=', 'project')]",
        required=True
    )

    project_id = fields.Many2one('project.project', string="Project")
    # bill_id = fields.Many2one('account.move', string="Vendor Bill", domain=[('move_type', '=', 'in_invoice')], required=True)
    amount = fields.Monetary(related='bill_id.amount_total', string="Total Amount")
    # invoice_date = fields.Date(related='bill_id.invoice_date', string="Invoice Date", store=True)

    currency_id = fields.Many2one(related='bill_id.currency_id', string="Currency",
                                  store=True)
    # ('state', '=', 'draft'), ('project_id', '=', project_id),

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")



class ProjectContractLine(models.Model):
    _name = 'project.contract.line'
    _description = 'Contract Line'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    date = fields.Date(string="Rent Date", required=True)
    amount = fields.Float(string="Rent Amount", required=True)
    invoice_created = fields.Boolean(string="Invoice Created", default=False)

    def action_create_invoice(self):
        print('deffffffffffff')
        self.ensure_one()
        if not self.project_id.partner_id:
            raise UserError("No partner found on the project. Please set a partner before creating an invoice.")

        invoice_vals = {
            'partner_id': self.project_id.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Rent for {self.date}',
                'price_unit': self.amount,

            })],
            'state': 'draft',
        }


        invoice = self.env['account.move'].create(invoice_vals)
        print(invoice,'invoiceeeeeeeee')
        self.invoice_created = True

        return invoice


class AccountMove(models.Model):
    _inherit = 'account.move'

    type_selection = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('project', 'Project'),
    ], string="Type", default='vehicle')

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    project_id = fields.Many2one('project.project', string="Project")

    responsible_selection = fields.Selection([
        ('driver', 'Driver'),
        ('customer', 'Customer'),
        ('company', 'Company'),
    ], string="Responsible", default='customer')

    responsible_customer_id = fields.Many2one('res.partner', string="Responsible Customer")
    responsible_driver_id = fields.Many2one('hr.employee', string="Responsible Driver",
                                            domain=[('is_driver', '=', True)])

    responsible_company_id = fields.Many2one('res.company', string="Responsible Company",
                                             default=lambda self: self.env.company)




# creating invoices for driver and customer only

    def action_post(self):
        if self.move_type == 'in_invoice' and self.state == 'draft':
            if self.type_selection == 'project':
                self.state = 'posted'
                return True

            print(self.responsible_selection, 'responsibleeeeeeeeee')

            if self.responsible_selection in ['customer', 'driver']:
                if self.responsible_selection == 'customer' and not self.responsible_customer_id:
                    raise UserError("Please select a responsible customer.")
                elif self.responsible_selection == 'driver' and not self.responsible_driver_id:
                    raise UserError("Please select a responsible driver.")

                invoice_line_vals = []
                for bill_line in self.invoice_line_ids:
                    invoice_line_vals.append((0, 0, {
                        'name': bill_line.name,
                        'price_unit': bill_line.price_unit,
                        'quantity': bill_line.quantity,
                        'product_id': bill_line.product_id.id,
                    }))
                print(invoice_line_vals,'invoice valsssssssssss')

                if self.responsible_selection == 'customer':
                    partner_id = self.responsible_customer_id.id
                    partner_name = self.responsible_customer_id.name
                    print(partner_name, 'partner name')
                elif self.responsible_selection == 'driver':
                    if not self.responsible_driver_id.user_id.partner_id:
                        partner_name = self.responsible_driver_id.name
                        partner_id = self.env['res.partner'].create({
                            'name': partner_name,
                        }).id
                    else:
                        partner_id = self.responsible_driver_id.user_id.partner_id.id
                        partner_name = self.responsible_driver_id.name
                        print(partner_name, 'partner name')

                invoice_vals = {
                    'partner_id': partner_id,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': invoice_line_vals,
                }
                print(invoice_vals,'invoiceeeeeee')

                self.env['account.move'].create(invoice_vals)

        return super(AccountMove, self).action_post()







# commented because of when the type is project its not confirming
#     def action_post(self):
#         if self.move_type == 'in_invoice' and self.state == 'draft':
#             if self.type_selection == 'project':
#                 # self.state = 'posted'
#                 self.state = 'draft'
#                 return True
#             print(self.responsible_selection,'responsibleeeeeeeeee')
#             if self.responsible_selection in ['customer', 'driver']:
#                 if self.responsible_selection == 'customer' and not self.responsible_customer_id:
#                     raise UserError("Please select a responsible customer before confirming the bill.")
#                 elif self.responsible_selection == 'driver' and not self.responsible_driver_id:
#                     raise UserError("Please select a responsible driver before confirming the bill.")
#
#                 invoice_line_vals = []
#                 for bill_line in self.invoice_line_ids:
#                     invoice_line_vals.append((0, 0, {
#                         'name': bill_line.name,
#                         'price_unit': bill_line.price_unit,
#                         'quantity': bill_line.quantity,
#                         'product_id': bill_line.product_id.id,
#                     }))
#
#                 if self.responsible_selection == 'customer':
#                     partner_id = self.responsible_customer_id.id
#                     partner_name = self.responsible_customer_id.name
#                     print(partner_name,'partner name')
#                 elif self.responsible_selection == 'driver':
#                     if not self.responsible_driver_id.user_id.partner_id:
#                         partner_name = self.responsible_driver_id.name
#                         partner_id = self.env['res.partner'].create({
#                             'name': partner_name,
#                         }).id
#                     else:
#                         partner_id = self.responsible_driver_id.user_id.partner_id.id
#                         partner_name = self.responsible_driver_id.name
#                         print(partner_name, 'partner name')
#
#                 # Create the invoice
#                 invoice_vals = {
#                     'partner_id': partner_id,
#                     'move_type': 'out_invoice',
#                     'invoice_date': fields.Date.today(),
#                     'invoice_line_ids': invoice_line_vals,
#                 }
#
#                 self.env['account.move'].create(invoice_vals)
#
#         return super(AccountMove, self).action_post()
#















