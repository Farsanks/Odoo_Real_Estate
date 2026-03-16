{
    'name': 'Real Estate Account',

    'depends': [
'account',
        'my_estate',    # our real estate module
           # odoo invoicing module
    ],

    'installable': True,

    'auto_install': True,  # auto installs when both estate + account are installed
}