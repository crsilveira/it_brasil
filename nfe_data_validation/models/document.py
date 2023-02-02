#
#    Copyright © 2022–; Brasil; IT Brasil; Todos os direitos reservados
#    Copyright © 2022–; Brazil; IT Brasil; All rights reserved
#

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.addons.spec_driven_model.models import spec_models
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class NFe(spec_models.StackedModel):
    _inherit = "l10n_br_fiscal.document"  # l10n_br_nfe

    def valida_dados_remetente(self):
        company = self.company_id.partner_id
        if self.document_type:
            if not company.state_id or not company.street_number or not company.inscr_est:
                self.company_id.partner_id.action_consult_cnpj()

    def valida_dados_destinatario(self):
        if not self.document_type:
            return True
        partner = self.partner_id
        if partner:
            if not partner.country_id:
                raise ValidationError(
                    'Informe o país no cadastro do parceiro!')
            msg = 'Os dados cadastrais do destinário estão incompletos. Favor preencher os seguintes campos:\n'
            count = 0
            if partner.company_type == 'person':
                if not partner.legal_name:
                    msg += '\n    - Nome Completo;'
                    count += 1
                if not partner.cnpj_cpf:
                    if partner.country_id.code == 'BR':
                        msg += '\n    - CPF;'
                        count += 1
            if partner.company_type == 'company':
                if not partner.legal_name:
                    msg += '\n    - Razão Social;'
                    count += 1
                if len(partner.legal_name) > 60:
                    msg += '\n    - A Razão Social deve ter no máximo 60 Caracteres, edite o contato antes de validar a fatura;'
                    count += 1
                if not partner.cnpj_cpf:
                    if partner.country_id.code == 'BR':
                        msg += '\n    - CNPJ;'
                        count += 1
                if not partner.inscr_est and partner.ind_ie_dest == '1':
                    if partner.country_id.code == 'BR':
                        msg += '\n    - Inscrição Estadual;'
                        count += 1
            if not partner.zip:
                if partner.country_id.code == 'BR':
                    msg += '\n    - CEP;'
                    count += 1
                else:
                    partner.zip = '99999999'
            if partner.zip == '-':
                partner.zip = '99999999'
            if not partner.street_name:
                msg += '\n    - Nome da Rua (Logradouro);'
                count += 1
            if not partner.street_number:
                msg += '\n    - Número da rua;'
                count += 1
            if not partner.district:
                if partner.country_id.code == 'BR':
                    msg += '\n    - Bairro;'
                    count += 1
            if not partner.city:
                if partner.country_id.code == 'BR':
                    msg += '\n    - Cidade;'
                    count += 1
                else:
                    partner.city = '9999999'
            if not partner.state_id:
                if partner.country_id.code == 'BR':
                    msg += '\n    - Estado;'
                    count += 1
            if not partner.phone:
                if partner.country_id.code == 'BR':
                    if partner.mobile:
                        partner.phone = partner.mobile
                    else:
                        msg += '\n    - Telefone;'
                        count += 1
            if count > 0:
                raise ValidationError(msg)
        else:
            raise ValidationError(
                'Não há Parceiro vinculado ao documento fiscal!')
    
    def valida_endereco_entrega(self):
        if not self.document_type:
            return True
        partner_address = self.partner_shipping_id

        if not partner_address:
            return True
        else:
            if partner_address.zip and partner_address.street_number and partner_address.country_id.code == 'BR':
                partner_address.zip_search()
                if not partner_address.legal_name:
                    partner_address.legal_name = self.partner_id.legal_name
                return True
            elif partner_address.country_id.code != 'BR':
                raise ValidationError(
                    'Por favor, remova o endereço de entrega antes de validar a fatura!')
            else:
                msg = 'Os dados cadastrais do endereço de entrega estão incompletos. Favor preencher os seguintes campos:\n'
                count = 0
                if not partner_address.street_name:
                    msg += '\n    - Nome da Rua (Logradouro);'
                    count += 1
                if not partner_address.street_number:
                    msg += '\n    - Número da rua;'
                    count += 1
                if not partner_address.district:
                    if partner_address.country_id.code == 'BR':
                        msg += '\n    - Bairro;'
                        count += 1
                if not partner_address.city:
                    if partner_address.country_id.code == 'BR':
                        msg += '\n    - Cidade;'
                        count += 1
                    else:
                        partner_address.city = '9999999'
                if not partner_address.state_id:
                    if partner_address.country_id.code == 'BR':
                        msg += '\n    - Estado;'
                        count += 1
                if count > 0:
                    raise ValidationError(msg)

    def valida_dados_produtos(self):
        if not self.document_type:
            return True
        products = self.fiscal_line_ids.product_id.product_tmpl_id
        if products:
            final_msg = ''
            for product in products:
                count = 0
                msg = ''
                if product.name:
                    msg += 'Os dados cadastrais do produto %s estão incompletos. Favor preencher os seguintes campos:\n - ' % (
                        product.name)
                    if not product.ncm_id:
                        msg += 'Ncm, '
                        count += 1
                    if not product.icms_origin:
                        msg += 'Origem do ICMS'
                        count += 1
                    if msg.endswith(','):
                        msg = msg.rstrip(',')
                    msg += '\n\n'
                    if count > 0:
                        final_msg += msg
                else:
                    count += 1
                    msg += 'Os dados cadastrais do produto com id %d estão incompletos. Favor preencher os seguintes campos:\n - Nome do Produto, ' % (
                        product.product_id.product_tmpl_id.id)
                    if not product.ncm_id:
                        msg += 'Ncm, '
                    if not product.icms_origin:
                        msg += 'Origem do ICMS'
                    if msg.endswith(','):
                        msg = msg.rstrip(',')
                    msg += '\n\n'
                    final_msg += msg
            if final_msg:
                raise ValidationError(final_msg)
        else:
            raise ValidationError(
                'Não há Produto vinculado ao documento fiscal!')
