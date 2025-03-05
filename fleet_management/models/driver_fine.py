from datetime import timedelta

from dateutil.relativedelta import relativedelta


from odoo import models, fields, api
from odoo.exceptions import UserError


class FleetDriverFine(models.Model):
    _name = 'fleet.driver.fine'
    _description = 'Driver Fine for Fleet Contract'

    partner_id = fields.Many2one('res.partner', string="Driver", required=True)
    contract_id = fields.Many2one('fleet.rental.contract', string="Contract", required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=True)
    date = fields.Date(string="Fine Date", required=True)
    amount = fields.Float(string="Fine Amount", required=True)
    description = fields.Text(string="Description")
