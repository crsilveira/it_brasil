# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _, api


class TaxNfeReport(models.TransientModel):
    _name = "tax.nfe.report"
    _description = "Report NFe"


    company_id = fields.Many2one('res.company', 'Company')
    tax_group_id = fields.Many2one('l10n_br_fiscal.tax.group', 'Grupo Impostos')
    date_start = fields.Date('Data inicial', required=True, store=True, readonly=False, compute="_compute_date_range")
    date_end = fields.Date('Data Final', required=True, store=True, readonly=False, compute="_compute_date_range")
    date_range_id = fields.Many2one('date.range', "Periodo")

    @api.depends("date_range_id")
    def _compute_date_range(self):
        for wizard in self:
            if wizard.date_range_id:
                wizard.date_start = wizard.date_range_id.date_start
                wizard.date_end = wizard.date_range_id.date_end
            else:
                wizard.date_start = wizard.date_end = None

    def action_report_nfe_view(self):
        taxes = self.env["tax.report.nfe"].search_read([
            ('document_date', '>=', self.date_start.strftime("%Y/%m/%d")),
            ('document_date', '<=', self.date_end.strftime("%Y/%m/%d")),
            ('company_id', '=', self.company_id.id)
        ])
        # print("impostos", taxes_icms)
        # print("ver valor", self.read()[0])
        
        if self.tax_group_id.name == 'ICMS':
            cfop_values = self.env["tax.report.nfe"].read_group([
                ('document_date', '>=', self.date_start.strftime("%Y/%m/%d")),
                ('document_date', '<=', self.date_end.strftime("%Y/%m/%d")),
                ('company_id', '=', self.company_id.id)
            ], ['cfop', 'icms_value', 'icms_base', 'amount_total'], ['cfop'])
            # import pudb;pu.db
            data = {
                'form_data': self.read()[0],
                'taxes': taxes,
                'cfop': cfop_values,
            }
            return self.env.ref('l10n_br_tax_report.report_tax_nfe').report_action(self, data=data)
        elif self.tax_group_id.name == 'IPI':
            cfop_values = self.env["tax.report.nfe"].read_group([
                ('document_date', '>=', self.date_start.strftime("%Y/%m/%d")),
                ('document_date', '<=', self.date_end.strftime("%Y/%m/%d")),
                ('company_id', '=', self.company_id.id)
            ], ['cfop', 'ipi_value', 'ipi_base', 'amount_total'], ['cfop'])
            # import pudb;pu.db
            data = {
                'form_data': self.read()[0],
                'taxes': taxes,
                'cfop': cfop_values,
            }
            # TODO mudar o nome do relatorio q vai abrir : o report_tax_nfe = ICMS
            return self.env.ref('l10n_br_tax_report.report_tax_nfe_ipi').report_action(self, data=data)
        elif self.tax_group_id.name == 'PIS':
            cfop_values = self.env["tax.report.nfe"].read_group([
                ('document_date', '>=', self.date_start.strftime("%Y/%m/%d")),
                ('document_date', '<=', self.date_end.strftime("%Y/%m/%d")),
                ('company_id', '=', self.company_id.id)
            ], ['cfop', 'pis_value', 'pis_base', 'amount_total'], ['cfop'])
            # import pudb;pu.db
            data = {
                'form_data': self.read()[0],
                'taxes': taxes,
                'cfop': cfop_values,
            }
            # TODO mudar o nome do relatorio q vai abrir : o report_tax_nfe = ICMS
            return self.env.ref('l10n_br_tax_report.report_tax_nfe_pis').report_action(self, data=data)
        elif self.tax_group_id.name == 'COFINS':
            cfop_values = self.env["tax.report.nfe"].read_group([
                ('document_date', '>=', self.date_start.strftime("%Y/%m/%d")),
                ('document_date', '<=', self.date_end.strftime("%Y/%m/%d")),
                ('company_id', '=', self.company_id.id)
            ], ['cfop', 'cofins_value', 'cofins_base', 'amount_total'], ['cfop'])
            # import pudb;pu.db
            data = {
                'form_data': self.read()[0],
                'taxes': taxes,
                'cfop': cfop_values,
            }
            # TODO mudar o nome do relatorio q vai abrir : o report_tax_nfe = ICMS
            return self.env.ref('l10n_br_tax_report.report_tax_nfe_cofins').report_action(self, data=data)