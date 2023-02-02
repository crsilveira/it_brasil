from odoo import fields, models, _


class CnaeSecundary(models.Model):
    _name = "cnae.cnpj.sec"
    _description = "Cnae Secundary"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="cascade",
    )

    code = fields.Char(size=16)
    name = fields.Text(string="Name", required=True)

    # _sql_constraints = [
    #     (
    #         "cnae_cnpj_sec_code_uniq",
    #         "unique (code)",
    #         _("CNAE already exists with this code !"),
    #     )
    # ]