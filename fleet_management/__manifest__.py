# -*- coding: utf-8 -*-
{
    'name': 'Fleet Rental',
    'version': '17.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Fleet Rental',
    'description': 'Managing Fleet',
    'depends': [
         'project','account','base','fleet','hr_timesheet'
    ],
    'data': [
        # 'data/ir_sequence.xml',
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/fleet_management.xml',
        'views/project_management.xml',

    ],
    'assets': {},
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
