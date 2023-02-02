
# © 2021 Carlos R. Silveira, Manoel dos Santos, ATSti Solucoes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Importar Planilha",
    "category": "Others",
    "author": "ATS Soluções",
    "website": "",
    "version": "14.0.0.0.0",
    "depends": ["l10n_br_account", "account_payment_mode", "l10n_br_fiscal", "sale"],
     'data': [
        "security/ir.model.access.csv",
        "views/account_move_import.xml",
        "wizard/account_move_import.xml",
    ],
    "installable": True,
}
