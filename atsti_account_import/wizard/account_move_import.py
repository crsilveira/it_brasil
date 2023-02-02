# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import xlrd
import tempfile
import base64

_logger = logging.getLogger(__name__)


class AccountImportInvoice(models.Model):
    _name = "account.move.import.wizard"
    _description = "Import Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Description",
        required=True,
        default=lambda self: _('Import Invoice'),
        tracking=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id
    )

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ('error', 'Error')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    row_initial = fields.Integer(
        string="Sheet Row Initial",
        help="Row initial to import, ignore the 2 first rows of the sheet",
        required=True,
        default=1
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        required=True,
        domain=[('type', 'in', ['sale', 'purchase'])]
    )
    document_type = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Type"
    )

    row_end = fields.Integer(
        string="Sheet Row End",
        help="Row end to import, exacly row from sheet",
        required=True,
        default=10
    )
    input_file = fields.Binary(
        string="File",
        required=True,
        help="Select the file to import"
    )
    input_file_name = fields.Char(
        string="File Name",
        help="Select the file to import",
        readonly=True
    )

    move_ids = fields.Many2many(
        comodel_name="account.move",
        relation="account_move_import_wizard_rel",
        column1="wizard_id",
        column2="move_id",
        string="Invoices",
        readonly=True,
        copy=False
    )

    move_count = fields.Integer(
        string="Invoices Count",
        compute="_compute_move_count",
        readonly=True,
        copy=False
    )

    import_error_msg = fields.Text(
        string="Import Error Message",
        copy=False
    )

    move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_move_line_import_wizard_rel",
        column1="wizard_id",
        column2="move_line_id",
        string="Invoice Lines",
        readonly=True,
        copy=False
    )

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.company_id = self.journal_id.company_id.id
            self.name = self.journal_id.name + ' - ' + \
                str(fields.Date.context_today(self))

    def action_account_move_import(self):
        msg = ''
        if self.input_file:
            filename = self.name.replace(' ', '_')
            file_path = tempfile.gettempdir() + '/file.xls'
            data = base64.decodebytes(self.input_file)
            self.input_file_name = filename.replace(
                '-', '_') + '_' + str(fields.Date.context_today(self)) + '.xls'
            f = open(file_path, 'wb')
            f.write(data)
            f.close()
            book = xlrd.open_workbook(file_path)
            first_sheet = book.sheet_by_index(0)
            line = {}
            vals = {}
            msg = ''
            contagem = 0
            move = self.env['account.move']
            product = self.env['product.product']
            partner = self.env['res.partner']
            user = self.env['res.users']
            payment = self.env['account.payment.mode']
            fiscal = self.env['account.fiscal.position']
            operation = self.env['l10n_br_fiscal.operation']
            operation_line = self.env['l10n_br_fiscal.operation.line']
            cfop = self.env['l10n_br_fiscal.cfop']
            document_type = self.env['l10n_br_fiscal.document.type']
            document_serie = self.env['l10n_br_fiscal.document.serie']
            _logger.info('numero de linhas da planilha %s', first_sheet.nrows)
            for rownum in range(first_sheet.nrows):
                if rownum > 1 and rownum < self.row_end and rownum > self.row_initial:
                    _logger.info('Linha atual %s', rownum)
                    rowValues = first_sheet.row_values(rownum)

                    # ID Required
                    if not rowValues[0]:
                        msg += _('- A <strong>coluna A é obrigatória</strong>, verifique a <strong>linha %s</strong><br>' % rownum)
                        continue
                    else:
                        vals['ref'] = rowValues[0]

                    # Partner Required
                    if not rowValues[2]:
                        msg += _('- A <strong>coluna C é obrigatóriaM</strong>, verifique a <strong>linha %s</strong><br>' % rownum)
                        continue
                    else:
                        partner_id = partner.search(
                            [('name', '=', rowValues[2]), ('parent_id', '=', False)], limit=1)
                        if partner_id:
                            vals['partner_id'] = partner_id.id
                        else:
                            msg += _('- Contato não encontrado - <strong>%s</strong> - <strong>Linha %s</strong><br>' %
                                     (rowValues[2], rownum))
                            continue

                    # Product Required
                    if not rowValues[16]:
                        line['product_id'] = False
                        msg += _('- A <strong>coluna Q é obrigatória</strong>, verifique a <strong>linha %s</strong><br>' % rownum)
                        continue
                    else:
                        if type(rowValues[16]) == float:
                            prod_code = str(int(rowValues[16]))
                        else:
                            prod_code = str(rowValues[16])

                        product_id = product.search(
                            [('default_code', '=', prod_code)], limit=1)
                        if product_id:
                            line['product_id'] = product_id.id
                        else:
                            line['product_id'] = False
                            msg += _('- Produto não encontrado - <strong>%s</strong> - <strong>Linha %s</strong><br>' %
                                     (prod_code, rownum))
                            continue

                    #L10N Brazil
                    # if rowValues[7]:
                    #     #obter os dois primeiros caracteres
                    #     _logger.warning('tipo de documento %s', rowValues[7][:2].upper())
                    #     document_type_id = document_type.search([('code', '=', rowValues[7][:2].upper())], limit=1)
                    #     if document_type_id:
                    #         line['fiscal_operation_id'] = False
                    #         line['fiscal_operation_line_id'] = False
                    #         vals['document_type_id'] = document_type_id.id
                    #         if not rowValues[1]:
                    #             msg += _('The second column (B) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             vals['document_number'] = rowValues[1]
                    #         if not rowValues[8]:
                    #             msg += _(
                    #                 '- The ninth column (I) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             operation.search([('name', 'ilike', rowValues[8])], limit=1)
                    #             if operation:
                    #                 _logger.warning('operacao %s', operation.id)
                    #                 vals['fiscal_operation_id'] = operation.id
                    #                 line['fiscal_operation_id'] = operation.id
                    #             else:
                    #                 msg += _(
                    #                     '- Any operation found - %s - Line %s<br>' % (rowValues[8], rownum))
                    #                 continue
                    #         if not rowValues[9] and rowValues[8] and document_type_id:
                    #             msg += _(
                    #                 '- The tenth column (J) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             operation_line.search([('name', 'ilike', rowValues[9]), ('fiscal_operation_id', '=', vals['fiscal_operation_id'])], limit=1)
                    #             if operation_line:
                    #                 _logger.warning('operacao linha %s', operation_line.id)
                    #                 line['fiscal_operation_line_id'] = operation_line.id
                    #             else:
                    #                 msg += _(
                    #                     '- Any operation line found - %s - Line %s<br>' % (rowValues[9], rownum))
                    #                 continue
                    #         if not rowValues[10]:
                    #             msg += _(
                    #                 '- The eleventh column (K) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             if rowValues[10] == 'Empresa':
                    #                 vals['issuer'] = 'company'
                    #             elif rowValues[10] == 'Parceiro':
                    #                 vals['issuer'] = 'partner'
                    #             else:
                    #                 msg += _(
                    #                     '- Issuer not found - %s - Line %s, use "Empresa" or "Parceiro"<br>' % (rowValues[10], rownum))
                    #         if not rowValues[11]:
                    #             msg += _(
                    #                 '- The twelfth column (L) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             document_series_id = document_serie.search(
                    #                 [('id', '=', rowValues[11])], limit=1)
                    #             if document_series_id:
                    #                 vals['document_serie_id'] = document_series_id.id
                    #             else:
                    #                 msg += _(
                    #                     '- Document Serie not found - %s - Line %s<br>' % (rowValues[11], rownum))
                    #                 continue
                    #         if rowValues[12]:
                    #             vals['document_key'] = rowValues[12]
                    #         if not rowValues[13]:
                    #             msg += _(
                    #                 '- The thirteenth column (M) is required, please check the line %s <br>' % rownum)
                    #             continue
                    #         else:
                    #             cfop_id = cfop.search([('code', '=', rowValues[13])], limit=1)
                    #             if cfop_id:
                    #                 vals['cfop_id'] = cfop_id.id
                    #             else:
                    #                 msg += _(
                    #                     '- CFOP not found - %s - Line %s<br>' % (rowValues[13], rownum))
                    #                 continue
                    #     else:
                    #         msg += _(
                    #             '- Document Type not found - %s - Line %s<br>' % (rowValues[7], rownum))
                    #         continue

                    if self.journal_id.type == 'sale':
                        vals['move_type'] = 'out_invoice'
                        vals['issuer'] = 'company'
            #                 position_fiscal = fiscal.search(
            #                     [('name', 'ilike', 'venda')], limit=1)
                    if self.journal_id.type == 'purchase':
                        vals['move_type'] = 'in_invoice'
                        vals['issuer'] = 'partner'
            #                 position_fiscal = fiscal.search(
            #                     [('name', 'ilike', 'compra')], limit=1)

                    vals['journal_id'] = self.journal_id.id
                    vals['document_type_id'] = 1
                    vals['fiscal_operation_id'] = 14
                    vals['currency_id'] = 6
                    vals['document_number'] = rowValues[1]
                    vals['journal_id'] = self.journal_id.id
                    vals['narration'] = 'Linha %s' % rownum

                    vals['invoice_date'] = datetime(
                        *xlrd.xldate_as_tuple(rowValues[3], book.datemode))
                    vals['date'] = datetime(
                        *xlrd.xldate_as_tuple(rowValues[4], book.datemode))
                    vals['invoice_date_due'] = datetime(
                            *xlrd.xldate_as_tuple(rowValues[5], book.datemode))

                    search_invoice = move.search(
                        [('ref', '=', vals['ref']), ('partner_id', '=', vals['partner_id'])], limit=1)

                    if search_invoice and search_invoice.state == 'draft' and line['product_id']:
                        search_invoice_line = search_invoice.invoice_line_ids.filtered(
                            lambda x: x.product_id.id == line['product_id'])
                        if search_invoice_line:
                            msg += _('- Fatura <stong>%s</strong> já existe para o parceiro <strong>%s</strong> com o produto <strong>%s</strong>, <strong>linha %s não foi importada</strong> - <a href="#" data-oe-model="account.move" data-oe-id="%s" class="oe_form_uri">Ver Fatura</a><br>' % (
                                search_invoice.ref, search_invoice.partner_id.name, search_invoice_line.product_id.name, rownum, search_invoice.id))
                            continue
                        else:
                            cfop_id = cfop.search(
                                    [('name', 'ilike', 'Provisão')], limit=1)
                            cfop_1949 = cfop.search(
                                [('code', '=', '1949')], limit=1)
                            search_invoice.invoice_line_ids = [(0, 0, {
                                'product_id': line['product_id'],
                                'quantity': rowValues[17],
                                'price_unit': rowValues[18],
                                # 'fiscal_operation_id': 14,
                                # 'fiscal_operation_line_id': 26,
                                # 'cfop_id': cfop_id.id if cfop_id else cfop_1949.id,
                                # 'fiscal_operation_id': line['fiscal_operation_id'] if line['fiscal_operation_id'] and document_type_id.code in ('55', '65') else False,
                                # 'fiscal_operation_line_id': line['fiscal_operation_line_id'] if line['fiscal_operation_line_id'] and document_type_id.code in ('55', '65') else False,
                                # 'cfop_id': line['cfop_id'] if line['cfop_id'] and document_type_id.code in ('55', '65') else False
                            })]
                            self.move_ids += search_invoice
                            search_invoice.message_post_with_view(
                                'mail.message_origin_link',
                                values={'self': search_invoice,
                                        'origin': self, 'edit': True},
                                subtype_id=self.env.ref('mail.mt_note').id
                            )
                            msg += _('- Fatura <strong>%s</strong> já criada para o contato <strong>%s, linha %s foi adicionada</strong>.<br>' % (
                                vals['ref'], rowValues[2], rownum))
                    elif search_invoice and search_invoice.state == 'draft' and not line['product_id']:
                        msg += _('- Fatura <strong>%s</strong> já foi criada, <strong>linha %s</strong> não tem produto e não foi importada.<br>' % (
                            vals['ref'], rownum))
                        continue
                    elif search_invoice and search_invoice.state == 'posted':
                        msg += _('- Fatura <strong>%s</strong> já está lançada para o contato <strong>%s</strong>, <strong>linha %s não foi importada</strong>.<br>' % (
                            vals['ref'], rowValues[2], rownum))
                        continue
                    else:
                        invoice = move.create(vals)
                        if invoice:
                            if not line['product_id']:
                                invoice.unlink()
                                msg += _('- Fatura <strong>%s</strong> não foi criada, <strong>linha %s</strong> não tem produto.<br>' % (
                                    vals['ref'], rownum))
                            else:
                                cfop_id = cfop.search(
                                    [('name', 'ilike', 'Provisão')], limit=1)
                                cfop_1949 = cfop.search(
                                    [('code', '=', '1949')], limit=1)
                                invoice.invoice_line_ids = [(0, 0, {
                                    'product_id': line['product_id'],
                                    'quantity': rowValues[17],
                                    'price_unit': rowValues[18],
                                    # 'fiscal_operation_id': 14,
                                    # 'fiscal_operation_line_id': 26,
                                    # 'cfop_id': cfop_id.id if cfop_id else cfop_1949.id,
                                })]
                                invoice._onchange_invoice_line_ids()
                                invoice.message_post_with_view(
                                    'mail.message_origin_link',
                                    values={'self': invoice, 'origin': self},
                                    subtype_id=self.env.ref('mail.mt_note').id
                                )
                                contagem += 1
                                self.move_ids = [(4, invoice.id)]
                                _logger.info('Invoice created: %s', invoice.id)

            msg += ('<br> Total de faturas importadas : %s' % (str(contagem)))
            self.message_post(
                body=msg,
                subject=_('Importação de faturas concluída!'),
                message_type='notification'
            )

            if contagem <= 0:
                self.state = 'error'
            else:
                self.state = 'posted'

            #             # if rowValues[7] == 55:
            #             #     vals['document_type_id'] = 31
            #             if rowValues[8]:
            #                 operacao = operation.search(
            #                     [('name', 'ilike', rowValues[8])], limit=1)
            #                 if operacao:
            #                     vals['fiscal_operation_id'] = operacao.id
            #             # if rowValues[10]:
            #             #     vals['document_serie_id'] = rowValues[10]
            #             vals['document_serie_id'] = 1
            #             if rowValues[11]:
            #                 vals['document_key'] = rowValues[11]
            #             if rowValues[12]:
            #                 vals['pedido_cliente'] = rowValues[12]
            #             if rowValues[13]:
            #                 pay = payment.search(
            #                     [('name', 'ilike', rowValues[13])], limit=1)
            #                 if pay:
            #                     vals['payment_mode_id'] = pay.id
            #             vals['payment_state'] = 'not_paid'
            #             vals['invoice_origin'] = 'importado'
            #         item = {}
            #         if type(rowValues[16]) == float:
            #             prd = str(int(rowValues[16]))
            #         else:
            #             prd = str(rowValues[16])

            #         prod = product.search(
            #             [('default_code', '=', prd)], limit=1)
            #         if prod:
            #             item['product_id'] = prod.id
            #         else:
            #             msg += ('Produto <strong>%s</strong> não localizado - <strong>Linha %s</strong> - <br>' % (
            #                 prd, rownum))
            #             continue
            #         accounts = prod.product_tmpl_id.get_product_accounts(
            #             fiscal_pos=position_fiscal)
            #         if self.journal_id.type == 'sale':
            #             item['account_id'] = accounts['income'].id
            #         if self.journal_id.type == 'purchase':
            #             item['account_id'] = accounts['expense'].id
            #         item['quantity'] = rowValues[17]
            #         item['price_unit'] = rowValues[16]
            #         item['fiscal_quantity'] = rowValues[17]
            #         item['ipi_value'] = rowValues[18]
            #         if rowValues[19]:
            #             cfop_id = cfop.search([('name', '=', rowValues[19])])
            #             if cfop_id:
            #                 item['cfop_id'] = cfop_id.id
            #         # item['nfe40_vProd'] = rowValues[20]
            #         user_id = user.search([('name', '=', rowValues[21])])
            #         if user_id:
            #             item['invoice_user_id'] = user_id.id
            #         line.append((0, 0, item))
            # if vals and line:
            #     vals['invoice_line_ids'] = line
            #     # invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)
            #     # invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
            #     mv = move.create(vals)
            #     contagem += 1
            #     if mv:
            #         self.move_ids += mv

    def action_post_all(self):
        for item in self.move_ids:
            if item.state == 'draft':
                item.action_post()
            elif item.state == 'cancel':
                item.button_draft()
                item.action_post()

    @api.depends('move_ids')
    def _compute_move_count(self):
        for item in self:
            item.move_count = len(item.move_ids)

    def action_view_move_ids(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_line_form")
        action['domain'] = [('id', 'in', self.move_ids.ids)]
        return action

    def action_cancel(self):
        if self.move_line_ids:
            for line in self.move_line_ids:
                if line.unlink():
                    self.state = 'cancel'

        if self.move_ids:
            for move in self.move_ids:
                move.button_draft()
                move.button_cancel()
                move.active = False

            if self.move_ids.filtered(lambda x: x.state != 'cancel'):
                raise ValidationError(
                    _('Not all invoices have been cancelled.'))
