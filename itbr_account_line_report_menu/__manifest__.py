
{
    'name': "Account Line Report Menu",
    'license': 'Other proprietary',
    'author': 'IT Brasil',
    'website': 'https://itbrasil.com.br',
    'category': 'Extra Tools',
    'summary': 'Cria menu relátório Receber e pagar em Contabilidade',
	'description' : 'Cria menu relátório Receber e pagar em Contabilidade',
    'depends': ['l10n_br_account', 'account_accountant', 'account_reports'],
    'qweb': [],
    'data': [
		#Security
		'security/ir.model.access.csv',
		#Views
		'views/account_move_line_views.xml',
		#Wizards
		'wizard/payment_account_move_line_views.xml'
	],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}