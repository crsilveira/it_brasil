from odoo import fields, models, api

class ImportDeclarationLine(models.Model):
    _name = 'declaration.line'
    _description = "Linha da declaração de importação"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_brl_currency_id",
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_brl_currency_id(self):
        for item in self:
            item.brl_currency_id = self.env.ref("base.BRL").id

    name = fields.Char('Adição/Reg. exportação', size=3)
    sequence_di = fields.Integer('Sequência', default=1, required=True)
    manufacturer_code = fields.Char('Cód. Fabricante/Chave NFe', size=60, required=True)
    amount_discount = fields.Monetary(string='Valor/Quantidade Exp.', currency_field="brl_currency_id", required=True)
    drawback_number = fields.Char('Número Drawback', size=11)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', store=True, readonly=True, default=lambda s: s.env.company)