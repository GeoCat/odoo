# -*- coding: utf-8 -*-

# noinspection PyStatementEffect
{
    'name': 'Software Licensing',
    'category': 'Sales/Subscriptions',
    'version': '0.1',
    'sequence': 151,
    'summary': 'Manage and check out subscription-based (desktop) software licenses',
    'description': """Software Licensing
    
    This module allows internal users to issue and manage software licenses 
    for desktop applications (e.g. GeoCat Bridge).
    Whenever a GeoCat Bridge subscription is sold, a license is automatically created.
    The customer can see the license key in the portal and generate a license file.
    GeoCat employees can suspend, revoke or (re-)issue licenses.
    """,
    'depends': [
        'base',
        'sale_subscription',
        'portal',
        'base_automation',
        # 'sale_management',
        # 'web_cohort',
    ],
    # 'data': [
    #     'views/contact_views.xml',
    # ],
    # 'demo': [
    #     'data/mail_demo.xml',
    # ],
    'application': True,
    'installable': True,
    'author': 'GeoCat B.V.',
    'maintainer': 'Sander Schaminée',
    'license': 'Other proprietary',
    # 'assets': {
    #     'web.assets_tests': [
    #         'contacts/static/tests/tours/**/*',
    #     ],
    # }
}
