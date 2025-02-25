# -*- coding: utf-8 -*-
{
    'name': 'Fleet Rental',
    'version': '17.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Fleet Rental',
    'description': 'Managing Fleet',
    'depends': [
         'project','account','base','fleet','hr_timesheet','hr'
    ],
    'data': [
        # 'data/ir_sequence.xml',
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'report/income_expense_report.xml',
        'report/fleet_maintainance_history_report.xml',
        'views/fleet_management.xml',
        'views/project_management.xml',
        'views/hr_employee.xml',
        'views/report_action.xml',

    ],
    'assets': {},
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
