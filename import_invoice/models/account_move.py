import logging
from odoo import models, _, api
from lxml import objectify
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


def convert(obj, conversion=None):
    if conversion:
        return conversion(obj.text)
    if isinstance(obj, objectify.StringElement):
        return str(obj)
    if isinstance(obj, objectify.IntElement):
        return int(obj)
    if isinstance(obj, objectify.FloatElement):
        return float(obj)
    raise u"Tipo não implementado %s" % str(type(obj))


def get(obj, path, conversion=None):
    paths = path.split(".")
    index = 0
    for item in paths:
        if not item:
            continue
        if hasattr(obj, item):
            obj = obj[item]
            index += 1
        else:
            return None
    if len(paths) == index:
        return convert(obj, conversion=conversion)
    return None


def remove_none_values(dict):
    res = {}
    res.update({k: v for k, v in dict.items() if v})
    return res


def cnpj_cpf_format(cnpj_cpf):
    if len(cnpj_cpf) == 14:
        cnpj_cpf = (cnpj_cpf[0:2] + '.' + cnpj_cpf[2:5] +
                    '.' + cnpj_cpf[5:8] +
                    '/' + cnpj_cpf[8:12] +
                    '-' + cnpj_cpf[12:14])
    else:
        cnpj_cpf = (cnpj_cpf[0:3] + '.' + cnpj_cpf[3:6] +
                    '.' + cnpj_cpf[6:9] + '-' + cnpj_cpf[9:11])
    return cnpj_cpf


def format_ncm(ncm):
    if len(ncm) == 4:
        ncm = ncm[:2] + '.' + ncm[2:4]
    elif len(ncm) == 6:
        ncm = ncm[:4] + '.' + ncm[4:6]
    else:
        ncm = ncm[:4] + '.' + ncm[4:6] + '.' + ncm[6:8]

    return ncm


class AccountMove(models.Model):
    _inherit = 'account.move'

    """ ================================================
                        Validado    
    ================================================="""

    def import_nfe(self, company_id, nfe, xml):
        _logger.info(["import_nfe"])

        if self.search([('document_key', '=', nfe.protNFe.infProt.chNFe.text)]):
            raise UserError('Documento Eletrônico já importado!')

        invoice = {
            # Campos obrigatórios
            "invoice_date": nfe.NFe.infNFe.ide.dhEmi.text,
            "date": nfe.NFe.infNFe.ide.dhEmi.text,
            "company_id": company_id.id,
            "currency_id": company_id.currency_id.id,
            "journal_id": self._search_default_journal(["purchase"]).id,
            "move_type": "in_invoice",
            "state": "draft",
            "state_edoc": "em_digitacao",
            "fiscal_operation_id": self.env["l10n_br_fiscal.operation"].search([("fiscal_type","=","purchase")], limit=1).id,

            # Não obrigatórios
            "document_type_id": company_id.document_type_id.id,
            "document_number": nfe.NFe.infNFe.ide.nNF.text,
            "document_key": nfe.protNFe.infProt.chNFe.text,
            "document_serie": nfe.NFe.infNFe.ide.serie.text,
        }

        invoice.update(self._get_company_invoice(nfe))
        invoice.update(self.get_partner_nfe(nfe))

        _logger.info(["Criando Fatura"])
        invoice = self.create(invoice)

        _logger.info(["Criando Att Xml"])
        xml_file_vals = {"name": f"NFe-{nfe.protNFe.infProt.chNFe.text}.xml", "datas": xml}
        xml_file = self.env["ir.attachment"].create(xml_file_vals)

        _logger.info(["Criando Evento de Autorização"])
        vals_event = {
            "company_id": company_id.id,
            "document_id": invoice.fiscal_document_id.id,
            "document_type_id": company_id.document_type_id.id,
            "document_number": nfe.NFe.infNFe.ide.nNF.text,
            "document_serie_id": self.env["l10n_br_fiscal.document.serie"].search([('code','=','1')], limit=1).id,
            "partner_id": invoice.partner_id.id or False,
            "protocol_number": nfe.protNFe.infProt.nProt.text,
            "file_response_id": xml_file.id,
            "file_request_id": xml_file.id
        }
        authorization_event = self.env["l10n_br_fiscal.event"].create(vals_event)

        _logger.info(["Atualizando Fatura"])
        invoice.update({"authorization_event_id": authorization_event.id})

        _logger.info(["Criando Linha Da Fatura"])
        for line in nfe.NFe.infNFe.det: 
            item = self.create_invoice_item(line, invoice) 

        return invoice

    def _get_company_invoice(self, nfe):
        dest_cnpj_cpf = cnpj_cpf_format(str(nfe.NFe.infNFe.dest.CNPJ.text).zfill(14))
        company = self.env['res.company'].sudo().search([('partner_id.cnpj_cpf', '=', dest_cnpj_cpf)])

        if not company: 
            raise UserError("XML não destinado nem emitido por esta empresa.")
        return dict(company_id=company.id,)

    def get_partner_nfe(self, nfe):
        cnpj_cpf = cnpj_cpf_format(str(nfe.NFe.infNFe.emit.CNPJ.text).zfill(14))
        partner_id = self.env['res.partner'].search([('cnpj_cpf', '=', cnpj_cpf)], limit=1)        
        if not partner_id:
            raise ValidationError(_("Parceiro não cadastrado"))
        
        return dict(partner_id=partner_id.id)

    def create_invoice_item(self, item, invoice):
        codigo = get(item.prod, 'cProd', str)
        seller_id = self.env['product.supplierinfo'].search([('name', '=', invoice.partner_id.id),('product_code', '=', codigo)])

        product_id = None
        if seller_id:
            product_id = seller_id.product_tmpl_id
            if len(product_id) > 1:
                message = '\n'.join(["Produto: %s - %s" % (x.default_code or '', x.name) for x in product_id])
                raise UserError("Existem produtos duplicados com mesma codificação, corrija-os antes de prosseguir:\n%s" % message)

        if not product_id and item.prod.cEAN and str(item.prod.cEAN) != 'SEM GTIN':
            product_id = self.env['product.product'].search(
                [('barcode', '=', item.prod.cEAN)], limit=1)
        
        if not product_id:
            raise UserError("Não existe nenhum produto cadatrado com o código: %s" % codigo)

        product = {
            'move_id': invoice.id, 
            'product_id': product_id.id,
            'quantity': item.prod.qCom,
            #
            'account_id': product_id.categ_id.property_account_expense_categ_id.id,
            'ncm_id': product_id.ncm_id.id,
            "fiscal_operation_id": self.env["l10n_br_fiscal.operation"].search([("fiscal_type","=","purchase")], limit=1).id,
        }
        _logger.info(["Criando A linha "])
        itens = self.env['account.move.line'].create(product) 
        return itens