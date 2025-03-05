from datetime import timedelta

from dateutil.relativedelta import relativedelta


from odoo import models, fields, api
from odoo.exceptions import UserError


class FleetRentalContract(models.Model):
    _name = 'fleet.rental.contract'
    _description = 'Fleet Rental Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Contract Name', required=True )
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehicles' )
    rent_types = fields.Selection(
        [('daily', 'Daily'),('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        string="Rent Type",
        default='weekly',
    )
    date_start = fields.Date(string='Start Date', )
    date_end = fields.Date(string='End Date')
    rental_cost = fields.Float(string='Rental Cost')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='State')




    # Expense and Contract Lines
    expense_entry_ids = fields.One2many('fleet.contract.expense.entry', 'contract_id', string="Expense Entries")
    contract_line_ids = fields.One2many('fleet.contract.line', 'contract_id', string="Invoice Entries")

    # other payables

    other_payables_ids = fields.One2many(
        'fleet.contract.other.payables',
        'contract_id',
        string="Other Payables"
    )







    # Odoo chatter fields
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', readonly=True)
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', readonly=True)

    def action_submit(self):
        self.write({'state': 'running'})
        return True

    def action_validate(self):
        self.write({'state': 'expired'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_complete(self):
        self.write({'state': 'completed'})
        return True

    def reset_to_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_schedule(self):
        self.ensure_one()

    
        if not self.rental_cost or not self.date_start or not self.date_end:
            raise ValueError("Please provide Rent Amount, Start Date, and End Date.")

        # Generate rent lines based on rent type
        if self.rent_types == 'daily':
            self._generate_daily_rent_lines()
        elif self.rent_types == 'weekly':
            self._generate_weekly_rent_lines()
        elif self.rent_types == 'monthly':
            self._generate_monthly_rent_lines()
        elif self.rent_types == 'yearly':
            self._generate_yearly_rent_lines()

        # if self.rent_types == 'weekly':
        #     self._generate_weekly_rent_lines()
        # elif self.rent_types == 'monthly':
        #     self._generate_monthly_rent_lines()
        # elif self.rent_types == 'yearly':
        #     self._generate_yearly_rent_lines()

        self.state = 'running'
        # self.state = 'scheduled'



    def _generate_daily_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date_end)

        while current_date <= end_date:
            self.env['fleet.contract.line'].create({
                'contract_id': self.id,
                'date': current_date,
                'amount': self.rental_cost,
            })
            current_date += timedelta(days=1)

    # Rent Line Generation (Weekly, Monthly, Yearly)
    def _generate_weekly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date_end)

        while current_date < end_date:
            self.env['fleet.contract.line'].create({
                'contract_id': self.id,
                'date': current_date,
                'amount': self.rental_cost,
            })
            current_date += timedelta(weeks=1)

    def _generate_monthly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date_end)

        while current_date < end_date:
            self.env['fleet.contract.line'].create({
                'contract_id': self.id,
                'date': current_date,
                'amount': self.rental_cost,
            })
            current_date = current_date.replace(
                year=current_date.year + (current_date.month // 12),
                month=((current_date.month) % 12) + 1,
                day=1
            )

    def _generate_yearly_rent_lines(self):
        current_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date_end)

        while current_date < end_date:
            self.env['fleet.contract.line'].create({
                'contract_id': self.id,
                'date': current_date,
                'amount': self.rental_cost,
            })
            current_date = current_date.replace(year=current_date.year + 1)

    @api.constrains('vehicle_ids')
    def _check_vehicle_stage(self):
        for contract in self:
            for vehicle in contract.vehicle_ids:
                if vehicle.vehicle_stages in ['under_maintenance', 'under_contract']:
                    raise UserError(
                        'You cannot select vehicles that are in "Under Maintenance" or "Under Contract" stages.'
                    )


class FleetContractExpenseEntry(models.Model):
    _name = 'fleet.contract.expense.entry'
    _description = 'Expense Entry for Fleet Rental Contract'

    contract_id = fields.Many2one('fleet.rental.contract', string="Contract", required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    item = fields.Char(string="Item", required=True)
    description = fields.Text(string="Description")
    amount = fields.Monetary(string="Amount", required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)



class FleetContractLine(models.Model):
    _name = 'fleet.contract.line'
    _description = 'Fleet Rental Contract Line'

    contract_id = fields.Many2one('fleet.rental.contract', string="Contract", required=True)
    date = fields.Date(string="Rent Date", required=True)
    amount = fields.Float(string="Rent Amount", required=True)
    is_invoice_created = fields.Boolean(default=False)


    def create_invoice_for_contract_lines(self):
        today = fields.Date.today()
        contract_lines = self.search([('is_invoice_created', '=', False), ('date', '<=', today)])

        for contract_line in contract_lines:
            if not contract_line.contract_id.partner_id:
                raise UserError("No partner found on the contract. Please set a partner before creating an invoice.")

            next_invoice = self.search([
                ('contract_id', '=', contract_line.contract_id.id),
                ('date', '>', contract_line.date),
            ], limit=1, order='date')

            next_date = next_invoice.date if next_invoice else today

            # filtering
            customer_payables = self.env['fleet.contract.other.payables'].search([
                ('contract_id', '=', contract_line.contract_id.id),
                ('date_payable', '>=', contract_line.date),
                ('date_payable', '<', next_date),
                ('responsible', '=', 'customer'),
            ])

            payable_amount = sum(customer_payables.mapped('amount'))
            total_invoice_amount = contract_line.amount + payable_amount

            invoice_vals = {
                'partner_id': contract_line.contract_id.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': today,
                'contract_id': contract_line.contract_id.id,
                'invoice_line_ids': [
                    (0, 0, {
                        'name': f'Rent for {contract_line.date}',
                        'price_unit': contract_line.amount,
                    })
                ],
            }

            for payable in customer_payables:
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'name': f'Other Payable - {payable.date_payable}',
                    'price_unit': payable.amount,
                }))

            invoice = self.env['account.move'].create(invoice_vals)

            contract_line.is_invoice_created = True
            customer_payables.write({'is_invoiced': True})

            if contract_line.contract_id.rent_types == 'weekly':
                contract_line.date += relativedelta(weeks=1)
            elif contract_line.contract_id.rent_types == 'monthly':
                contract_line.date += relativedelta(months=1)
            elif contract_line.contract_id.rent_types == 'yearly':
                contract_line.date += relativedelta(years=1)
    # @api.model
    # def create_invoice_for_contract_lines(self):
    #     today = fields.Date.today()
    #     contract_lines = self.search([('is_invoice_created', '=', False)])
    #
    #     for contract_line in contract_lines:
    #         if contract_line.date == today and not contract_line.is_invoice_created:
    #             if not contract_line.contract_id.partner_id:
    #                 raise UserError(
    #                     "No partner found on the contract. Please set a partner before creating an invoice.")
    #
    #             invoice_vals = {
    #                 'partner_id': contract_line.contract_id.partner_id.id,
    #                 'move_type': 'out_invoice',
    #                 'invoice_date': today,
    #                 'contract_id': contract_line.contract_id.id,
    #                 'invoice_line_ids': [(0, 0, {
    #                     'name': f'Rent for {contract_line.date}',
    #                     'price_unit': contract_line.amount,
    #                 })],
    #             }
    #             self.env['account.move'].create(invoice_vals)
    #
    #             contract_line.is_invoice_created = True
    #
    #             # Update next rent date based on rent type
    #             if contract_line.contract_id.rent_types == 'weekly':
    #                 contract_line.date += relativedelta(weeks=1)
    #             elif contract_line.contract_id.rent_types == 'monthly':
    #                 contract_line.date += relativedelta(months=1)
    #             elif contract_line.contract_id.rent_types == 'yearly':
    #                 contract_line.date += relativedelta(years=1)
    #


# corrected function customer payables only generated invoice 5th

    def button_create_invoice(self):
        self.ensure_one()

        next_invoice = self.env['fleet.contract.line'].search([
            ('contract_id', '=', self.contract_id.id),
            ('date', '>', self.date),
        ], limit=1, order='date')
        print(next_invoice,'next invoiceeeee')

        next_date = next_invoice.date if next_invoice else fields.Date.today()
        print(next_date,'next dateeee')

        customer_payables = self.env['fleet.contract.other.payables'].search([
            ('contract_id', '=', self.contract_id.id),
            ('date_payable', '>=', self.date),
            ('date_payable', '<', next_date),
            ('responsible', '=', 'customer'),
        ])

        payable_amount = sum(customer_payables.mapped('amount'))
        total_invoice_amount = self.amount + payable_amount
        print(total_invoice_amount,'invoice totalllll')

        invoice_line_vals = [
            (0, 0, {
                'name': f'Rent for {self.date}',
                'price_unit': self.amount,
            })
        ]

        for payable in customer_payables:
            invoice_line_vals.append((0, 0, {
                'name': f'Other Payable - {payable.date_payable}',
                'price_unit': payable.amount,
            }))

        self.env['account.move'].create({
            'partner_id': self.contract_id.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.date,
            'date': self.date,
            'contract_id': self.contract_id.id,
            'invoice_line_ids': invoice_line_vals,
        })


        customer_payables.write({'is_invoiced': True})


        self.is_invoice_created = True

# worked function on 4th not modified
    # def button_create_invoice(self):
    #     self.ensure_one()
    #
    #     # Find the next invoice date
    #     next_invoice = self.env['fleet.contract.line'].search([
    #         ('contract_id', '=', self.contract_id.id),
    #         ('date', '>', self.date),
    #     ], limit=1, order='date')
    #
    #     next_date = next_invoice.date if next_invoice else fields.Date.today()
    #
    #
    #     customer_payables = self.env['fleet.contract.other.payables'].search([
    #         ('contract_id', '=', self.contract_id.id),
    #         ('date_payable', '>=', self.date),
    #         ('date_payable', '<', next_date),
    #         ('responsible', '=', 'customer'),
    #     ])
    #
    #     print(customer_payables, 'Filtered customer payables')
    #
    #     payable_amount = sum(customer_payables.mapped('amount'))
    #     total_invoice_amount = self.amount + payable_amount
    #
    #     print(total_invoice_amount, 'Total Invoice Amount')
    #
    #     # Create the invoice
    #     self.env['account.move'].create({
    #         'partner_id': self.contract_id.partner_id.id,
    #         'move_type': 'out_invoice',
    #         'invoice_date': self.date,
    #         'date': self.date,
    #         'contract_id': self.contract_id.id,
    #         'invoice_line_ids': [(0, 0, {
    #             'price_unit': total_invoice_amount,
    #         })],
    #     })
    #
    #     customer_payables.write({'is_invoiced': True})
    #
    #     self.is_invoice_created = True





class AccountMove(models.Model):
    _inherit = 'account.move'

    is_contract_expense = fields.Boolean(string='Is Contract Expense')
    contract_id = fields.Many2one('fleet.rental.contract', string="Contract")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type == 'in_invoice' and self.is_contract_expense:
            if self.contract_id:
                for line in self.invoice_line_ids:
                    self.env['fleet.contract.expense.entry'].create({
                        'contract_id': self.contract_id.id,
                        'item': line.name,
                        'description': line.name,
                        'amount': line.price_subtotal,
                        # 'currency_id': self.currency_id.id,
                    })
            else:
                raise UserError("Contract not set. Please set the contract for this invoice.")

        return res






# other payables

class FleetContractOtherPayables(models.Model):
    _name = 'fleet.contract.other.payables'
    _description = 'Other Payables for Fleet Rental Contract'

    contract_id = fields.Many2one('fleet.rental.contract', string="Contract")
    date_payable = fields.Date(string="Date")
    description = fields.Char(string="Description")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", domain="[('id', 'in', vehicle_ids)]")
    responsible = fields.Selection([
        ('driver', 'Driver'),
        ('customer', 'Customer'),], string="Responsible", default='customer')
    amount = fields.Float(string="Amount")
    is_invoiced = fields.Boolean(default=False, string="Invoiced")
    is_fine_created = fields.Boolean(default=False, string="Fine Created")

    driver_id = fields.Many2one('res.partner', string="Driver", domain="[('is_driver', '=', True)]",
                                compute="_compute_driver_id", store=True)

    @api.depends('vehicle_id', 'responsible')
    def _compute_driver_id(self):
        for record in self:
            if record.responsible == 'driver' and record.vehicle_id:
                record.driver_id = record.vehicle_id.driver_id
            else:
                record.driver_id = False

    def button_create_fine(self):
        if self.responsible != 'driver':
            raise UserError("Fines can only be created for driver-related payables.")

        if not self.vehicle_id:
            raise UserError("No vehicle associated with this payable.")

        if not self.contract_id:
            raise UserError("No contract associated with this payable.")


        if not self.driver_id:
            raise UserError("No driver assigned to this payable.")

        fine_record = self.env['fleet.driver.fine'].create({
            'partner_id': self.driver_id.id,
            'vehicle_id': self.vehicle_id.id,
            'contract_id': self.contract_id.id,
            'date': self.date_payable,
            'amount': self.amount,
            'description': f'Fine for {self.description}',
        })

        self.is_invoiced = True
        self.is_fine_created = True












