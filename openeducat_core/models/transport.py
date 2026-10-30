# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OpTransportRoute(models.Model):
    _name = 'op.transport.route'
    _description = 'School Transport Route'
    _order = 'name'

    name = fields.Char(string='Route Name', required=True)
    code = fields.Char(string='Route Code')
    start_point = fields.Char(string='Starting Point')
    end_point = fields.Char(string='Destination / Campus', default='Main School Campus')
    stop_ids = fields.One2many('op.transport.stop', 'route_id', string='Pickup / Drop Stops')
    bus_ids = fields.One2many('op.transport.bus', 'route_id', string='Assigned Buses')
    note = fields.Text(string='Notes & Details')
    active = fields.Boolean(default=True)


class OpTransportStop(models.Model):
    _name = 'op.transport.stop'
    _description = 'Transport Route Stop'
    _order = 'sequence, name'

    name = fields.Char(string='Stop Name', required=True)
    route_id = fields.Many2one('op.transport.route', string='Route', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    pickup_time = fields.Char(string='Morning Pickup Time', default='07:30 AM')
    drop_time = fields.Char(string='Afternoon Drop Time', default='03:30 PM')
    monthly_fare = fields.Float(string='Monthly Transport Fee', default=1500.0)


class OpTransportBus(models.Model):
    _name = 'op.transport.bus'
    _description = 'School Bus & Live Tracking'
    _order = 'name'

    name = fields.Char(string='Bus Identifier / Name', required=True, default='School Bus')
    vehicle_number = fields.Char(string='License Plate / Registration No.', required=True)
    route_id = fields.Many2one('op.transport.route', string='Assigned Route')
    capacity = fields.Integer(string='Passenger Capacity', default=40)
    driver_name = fields.Char(string='Driver Name', required=True)
    driver_phone = fields.Char(string='Driver Mobile No.')
    conductor_name = fields.Char(string='Attendant / Conductor')
    conductor_phone = fields.Char(string='Attendant Contact')
    status = fields.Selection([
        ('on_route', 'On Route / Moving'),
        ('idle', 'At Campus / Parked'),
        ('maintenance', 'In Maintenance')
    ], string='Current Status', default='on_route')
    current_location = fields.Char(string='Live Location / Nearest Stop', default='Approaching Stop 3 (Central Circle)')
    last_updated = fields.Datetime(string='Location Last Updated', default=fields.Datetime.now)
    live_gps_url = fields.Char(string='Live GPS Map Link', default='https://maps.google.com')
    student_count = fields.Integer(string='Allocated Students', compute='_compute_student_count')
    active = fields.Boolean(default=True)

    def _compute_student_count(self):
        reg_obj = self.env['op.transport.registration']
        for record in self:
            record.student_count = reg_obj.search_count([('bus_id', '=', record.id), ('status', '=', 'active')])


class OpTransportRegistration(models.Model):
    _name = 'op.transport.registration'
    _description = 'Student Transport Bus Pass Registration'
    _order = 'create_date desc'

    student_id = fields.Many2one('op.student', string='Student', required=True)
    route_id = fields.Many2one('op.transport.route', string='Route', required=True)
    stop_id = fields.Many2one('op.transport.stop', string='Pickup / Drop Stop', required=True)
    bus_id = fields.Many2one('op.transport.bus', string='Assigned School Bus')
    card_number = fields.Char(string='Bus Pass No.')
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='active')
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    end_date = fields.Date(string='Valid Till')
    note = fields.Text(string='Special Instructions')
