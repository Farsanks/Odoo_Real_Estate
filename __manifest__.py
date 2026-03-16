{
    'name': "my_estate",
    'application': True,
    'summary': "Real Estate Management System for managing properties and offers",
    'description': "Manage properties, track prices, and handle buyer offers in a real estate system",
    'version': '0.1',
    'depends': ['base', 'sale'],
    'category': 'My Estate',
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
    'sequence': 1,
    'data': [
        'views/res_users_view.xml',
        'views/property_tags.xml',

        'views/estate_properties.xml',

        'views/property_type.xml',
        'views/estate_views.xml',


        'security/ir.model.access.csv',
        'views/estate_menus.xml',
    ]
}
