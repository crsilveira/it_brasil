from odoo import fields, models, _


class CnpjSocios(models.Model):
    _name = "cnpj.socios"
    _description = "Quadro Societario"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="cascade",
    )

    name = fields.Text(string="Name", required=True, index=True)
    qualificacao = fields.Text(string="Qualificacao", required=True, index=True)