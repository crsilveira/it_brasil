# @ 2022 IT Brasil - www.itbrasil.com.br -
#   Renan Teixeira <renan.teixeira@itbrasil.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    cnpj_holder = fields.Char(
        string="CNPJ Holder",
        size=14,
        help="CNPJ Holder without punctuation",
    )

    plugboleto_holder_token = fields.Char(
        string="Plugboleto Holder Token",
        help="Plugboleto Holder Token",
    )