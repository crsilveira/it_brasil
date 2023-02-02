# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class TaxesReportNfe(models.Model):
    _name = "tax.report.nfe"
    _description = "Report NFe"
    _auto = False
    _order = 'document_date, document_number, cfop'

    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    document_type_id = fields.Many2one("l10n_br_fiscal.document.type", string="Document Type", readonly=True)
    document_date = fields.Datetime(string="Document Date", readonly=True)
    document_serie = fields.Char(string="Serie Number", readonly=True)
    document_number = fields.Char(string="Document Number", readonly=True)
    operation_name = fields.Char(string="Operation Name", readonly=True)
    status_name = fields.Char(string="Status Name", readonly=True)
    fiscal_operation_id = fields.Many2one("l10n_br_fiscal.operation", string="Fiscal Operation", readonly=True)
    cfop = fields.Char(string="CFOP")
    amount_total = fields.Float(string="Amount Total", readonly=True)
    icms_base = fields.Float(string="ICMS Base", readonly=True)
    icms_percent = fields.Float(string="ICMS %", readonly=True)
    icms_value = fields.Float(string="ICMS Valor", readonly=True)
    ipi_base = fields.Float(string="IPI Base", readonly=True)
    ipi_percent = fields.Float(string="IPI %", readonly=True)
    ipi_value = fields.Float(string="IPI Valor", readonly=True)
    pis_base = fields.Float(string="PIS Base", readonly=True)
    pis_percent = fields.Float(string="PIS %", readonly=True)
    pis_value = fields.Float(string="PIS Valor", readonly=True)
    cofins_base = fields.Float(string="COFINS Base", readonly=True)
    cofins_percent = fields.Float(string="COFINS %", readonly=True)
    cofins_value = fields.Float(string="COFINS Valor", readonly=True)
    # amount_ipi_base = fields.Monetary(string="IPI Base", readonly=True)
    # amount_pis_base = fields.Monetary(string="PIS Base", readonly=True)
    # amount_cofins_base = fields.Monetary(string="COFINS Base", readonly=True)
    # amount_icms_base = fields.Monetary(string="ICMS Base", readonly=True)
    # amount_ipi_base = fields.Monetary(string="IPI Base", readonly=True)
    # amount_pis_base = fields.Monetary(string="PIS Base", readonly=True)
    # amount_cofins_base = fields.Monetary(string="COFINS Base", readonly=True)    
    # icms_base = fields.Monetary(string="ICMS Base", readonly=True)
    # icms_percent = fields.Float(string="ICMS %", readonly=True)
    # icms_value = fields.Monetary(string="ICMS Value", readonly=True)
    # ipi_base = fields.Monetary(string="IPI Base", readonly=True)
    # ipi_percent = fields.Float(string="IPI %", readonly=True)
    # ipi_value = fields.Monetary(string="IPI Value", readonly=True)

    def init(self):
        query = """
    SELECT
        dl.id AS id,
        d.company_id,
        d.document_type_id,
        d.document_date,
        d.document_serie,
        d.document_number,
        op.name as operation_name,
        'Autorizado' AS status_name,
        d.fiscal_operation_id,
        cfop.code AS cfop,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.fiscal_price * dl.fiscal_quantity)
		  ELSE SUM(dl.fiscal_price * dl.fiscal_quantity) * (-1) END AS amount_total,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.icms_base) 
		  ELSE SUM(dl.icms_base) * (-1) END AS icms_base,
        dl.icms_percent,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.icms_value) 
			ELSE SUM(dl.icms_value) * (-1) END AS icms_value,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.ipi_base) 
		  ELSE SUM(dl.ipi_base) * (-1) END AS ipi_base,
        dl.ipi_percent,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.ipi_value) 
			ELSE SUM(dl.ipi_value) * (-1) END AS ipi_value,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.pis_base) 
		  ELSE SUM(dl.pis_base) * (-1) END AS pis_base,
        dl.pis_percent,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.pis_value) 
			ELSE SUM(dl.pis_value) * (-1) END AS pis_value,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.cofins_base) 
		  ELSE SUM(dl.cofins_base) * (-1) END AS cofins_base,
        dl.cofins_percent,
        CASE WHEN am.move_type = 'out_invoice' THEN SUM(dl.cofins_value) 
			ELSE SUM(dl.cofins_value) * (-1) END AS cofins_value
    FROM l10n_br_fiscal_document d
    INNER JOIN account_move am ON am.fiscal_document_id = d.id
    LEFT JOIN l10n_br_fiscal_document_line dl ON dl.document_id = d.id 
    LEFT JOIN l10n_br_fiscal_cfop cfop ON dl.cfop_id = cfop.id 
    LEFT JOIN l10n_br_fiscal_operation op ON d.fiscal_operation_id = op.id
    WHERE
    	(am.move_type in ('in_invoice', 'out_invoice')) and
		(am.state = 'posted') and
		(am.document_type = '55') and
	    ((d.state_edoc in ('autorizada'))  OR 
		(d.issuer = 'partner'))
    GROUP BY
        d.company_id,
        d.document_date, 
        d.document_serie,
        d.document_number,
        cfop.code,
        dl.icms_percent,
        dl.ipi_percent,
        dl.pis_percent,
        dl.cofins_percent,
        d.fiscal_operation_id,
        am.move_type,
        dl.id,
        d.document_type_id,
        op.name,
        d.status_name,
        d.state_edoc
        """
        # d.amount_total,
        # d.amount_icms_base,
        # d.amount_ipi_base,
        # d.amount_pis_base,
        # d.amount_cofins_base,
        # d.icms_base,
        # d.icms_percent,
        # d.icms_value,
        # d.ipi_base
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))
