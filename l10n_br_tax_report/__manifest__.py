# © 2021 Carlos R. Silveira, Manoel dos Santos, ATSti Solucoes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'NFe Taxes Report',
    'version': '1.0',
    'category': 'Others',
    'sequence': 2,
    'summary': 'ATSti Sistemas',
    'description': """
        Relatorios de Impostos por CFOP
   """,
    'author': 'ATS Soluções',
    'website': '',
    'depends': ['l10n_br_nfe'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/tax_report.xml',
        'report/tax_report_icms_templates.xml',
        'report/tax_report_ipi_templates.xml',
        'report/tax_report_pis_templates.xml',
        'report/tax_report_cofins_templates.xml',
        'report/tax_report_nfe.xml',
    ],
    'installable': True,
    'application': False,
}

