{
    'name': "yc_root",

    'summary': """
    """,

    'description': """
        YC_ROOT v.6
    """,

    'author': "ArJhe",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base'],

    'data': [
        'views/produce/purchase.xml',
        'views/produce/weight_cargo.xml',
        'views/produce/purchase_store.xml',
        'views/produce/purchase_report.xml',
        'views/driver.xml',
        'views/hr_main.xml',
        'views/fake.xml',

        'menuitem/root_core.xml',

    ],

    # only loaded in demonstration mode
    'demo': [

    ],
}