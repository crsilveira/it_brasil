from asyncio.log import logger
from copy import copy
from datetime import datetime
from email.policy import default
import json
import re
import logging

import requests

from odoo import api, models, _, fields
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    cnpjws_atualizadoem = fields.Datetime(
        string="Atualizado na base pública em",
        help="Data da última atualização das informações",
        readonly=True,
        copy=False
    )
    cnpjws_nome_fantasia = fields.Char(
        string="Nome Fantasia",
        readonly=True,
        copy=False
    )
    cnpjws_situacao_cadastral = fields.Char(
        string="Situação Cadastral",
        readonly=True,
        copy=False
    )
    cnpjws_tipo = fields.Char(
        string="Tipo de CNPJ",
        readonly=True,
        copy=False
    )

    cnpjws_porte = fields.Char(
        string="Porte da Empresa",
        readonly=True,
        copy=False
    )

    cnpjws_atualizado_odoo = fields.Datetime(
        string="Atualizado no Odoo em",
        help="Data da última atualização das informações no Odoo",
        readonly=True,
        copy=False
    )

    cnpjws_razao_social = fields.Char(
        string="Razão Social Completa",
        readonly=True,
        copy=False
    )

    cnpjws_size_legal_name = fields.Integer(
        string="Tamanho Razão Social",
        copy=False,
        default=0
    )

    cnpjws_manual_razao_social = fields.Boolean(
        string="Precisa de ajuste Razão Social",
        help="Se essa opção estiver marcada, significa que a Razão Social possuí mais de 60 caracteres e você precisa ajustar manualmente.",
        copy=False,
        default=False
    )

    cnpjws_capital_social = fields.Float(
        string="Capital Social",
        readonly=True,
        copy="False",
        default=0
    )

    cnae_cnpj_main_id = fields.Many2one(
        comodel_name="cnae.cnpj",
        domain=[("internal_type", "=", "normal")],
        string="Main CNAE",
    )

    cnae_cnpj_sec_id = fields.One2many(
        string="CNAE secundário",
        comodel_name="cnae.cnpj.sec",
        inverse_name="partner_id",
    )

    cnpj_socios_id = fields.One2many(
        string="Quadro Societario",
        comodel_name="cnpj.socios",
        inverse_name="partner_id",
    )

    cnpjws_email = fields.Char(
        string="Email Cadastral",
        readonly=True,

    )

    cnpjws_telefone = fields.Char(
        string="Telefone Cadastral",
        readonly=True,
    )

    def action_consult_cnpj_cnae(self):
        cnpjws_url = 'https://publica.cnpj.ws/cnpj/'
        if self.company_type == 'company':
            if self.cnpj_cpf:
                cnpj = re.sub('[^0-9]', '', self.cnpj_cpf)
                response = requests.get(cnpjws_url + cnpj)
                cnpjws_result = json.loads(response.text)
                if response.status_code == 200:
                    if len(cnpjws_result['razao_social']) > 60:
                        self.cnpjws_manual_razao_social = True

                    self.legal_name = cnpjws_result['razao_social']
                    self.cnpjws_razao_social = cnpjws_result['razao_social']

                    self.cnpjws_size_legal_name = len(self.legal_name)

                    cnpjws_estabelecimento = cnpjws_result['estabelecimento']
                    cnpjws_pais = cnpjws_result['estabelecimento']['pais']['comex_id']
                    cnpjws_estado = cnpjws_estabelecimento['estado']
                    cnpjws_cidade = cnpjws_estabelecimento['cidade']

                    search_country = self.env['res.country'].search(
                        [('siscomex_code', '=', cnpjws_pais)])
                    if search_country:
                        self.country_id = search_country.id

                    if cnpjws_estado['ibge_id']:
                        search_state = self.env['res.country.state'].search(
                            [('ibge_code', '=', cnpjws_estado['ibge_id'])])
                        if search_state:
                            self.state_id = search_state.id

                    if cnpjws_cidade:
                        self.city = cnpjws_cidade['nome']
                        search_city = self.env['res.city'].search(
                            [('ibge_code', '=', cnpjws_cidade['ibge_id'])])
                        if search_city:
                            self.city_id = search_city.id

                    self.zip = cnpjws_estabelecimento['cep']

                    if cnpjws_estabelecimento['tipo_logradouro']:
                        cnpj_t_logra = cnpjws_estabelecimento['tipo_logradouro']
                        cnpj_logra = cnpjws_estabelecimento['logradouro']

                        self.street_name = cnpj_t_logra + " " + cnpj_logra

                    self.street_number = cnpjws_estabelecimento['numero']

                    self.district = cnpjws_estabelecimento['bairro']
                    self.street2 = cnpjws_estabelecimento['complemento']

                    self.cnpjws_email = cnpjws_estabelecimento['email']
                    self.cnpjws_telefone = cnpjws_estabelecimento['ddd1'] + " " + cnpjws_estabelecimento['telefone1']

                    cnpjws_socios = cnpjws_result['socios']

                    cnpjws_simples = cnpjws_result['simples']
                    cnpjws_ie = cnpjws_estabelecimento['inscricoes_estaduais']

                    cnpjws_cnae = cnpjws_estabelecimento['atividade_principal']
                    cnpjws_cnae_sec = cnpjws_estabelecimento['atividades_secundarias']

                    fiscal_info = []

                    fiscal_info.append(cnpjws_simples)
                    fiscal_info.append(cnpjws_ie)
                    fiscal_info.append(cnpjws_cnae)
                    fiscal_info.append(cnpjws_cnae_sec)
                    fiscal_info.append(cnpjws_socios)

                    self.cnae_cnpj(fiscal_info)
                    self.define_cnae_sec(fiscal_info)
                    self.define_inscricao_estadual(fiscal_info)
                    self.define_socios(fiscal_info)
                    
                    self.cnpjws_atualizadoem = datetime.strptime(
                        cnpjws_result['atualizado_em'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    self.cnpjws_nome_fantasia = cnpjws_estabelecimento['nome_fantasia']
                    self.cnpjws_tipo = cnpjws_estabelecimento['tipo']
                    self.cnpjws_situacao_cadastral = cnpjws_estabelecimento['situacao_cadastral']
                    self.cnpjws_porte = cnpjws_result['porte']['descricao']
                    self.cnpjws_atualizado_odoo = datetime.now()
                    self.cnpjws_capital_social = cnpjws_result['capital_social']
                else:
                    raise ValidationError(
                        "Erro: " + cnpjws_result['titulo'] + '\n' + cnpjws_result['detalhes'] + '\n' 'Se a empresa for do Brasil, informe o CNPJ correto. Caso contrário, complete o cadastro manualmente.')
            else:
                raise UserError("Por favor, informe o CNPJ da empresa.")
        else:
            raise ValidationError(
                "Apenas contatos do tipo Empresa com CNPJ podem ser consultados.")

    def cnae_cnpj(self, fiscal_info):
        if fiscal_info[2]:
            search_cnae = self.env["cnae.cnpj"].search(
                [('code', '=', fiscal_info[2]['subclasse'])])

            if search_cnae:
                try:
                    incluir_cnae_principal = self.write(
                        {"cnae_cnpj_main_id": search_cnae.id})
                    _logger.info("CNAE Principal Adicionado: " +
                                 str(incluir_cnae_principal))
                except Exception:
                    incluir_cnae_principal = False
                    raise ValidationError(
                        "Erro ao incluir cnae: %s", fiscal_info[2]['subclasse'])

    def define_cnae_sec(self, fiscal_info):
        result_cnae = fiscal_info[3]
        search_cnae_sec_del = self.env['cnae.cnpj.sec'].search(
                [('partner_id', '=', self.id)]
            )
        if search_cnae_sec_del:
            for cnae_del in search_cnae_sec_del:
                cnae_del.unlink()
        #count number of cnaes in result cnae if not exist, create
        if result_cnae:
            count_cnae = len(result_cnae)
            for i in range(count_cnae):
                incluir_cnae_sec = self.write({
                    'cnae_cnpj_sec_id': [(0, 0, {
                        'partner_id': self.id,
                        'code': result_cnae[i]['subclasse'],
                        'name': result_cnae[i]['descricao'],
                    })]
                })
                if incluir_cnae_sec:
                    _logger.info("CNAE Secundário Adicionado: " +
                                 str(incluir_cnae_sec))
                else:
                    _logger.warning("CNAE Secundário não foi adicionado:")
                

    #define socios da empresa
    def define_socios(self, fiscal_info):
        result = fiscal_info[4]
        _logger.warning("Socios: %s", result)
        search_cnpj_socios_del = self.env['cnpj.socios'].search(
                [('partner_id', '=', self.id)]
            )
        if search_cnpj_socios_del:
            for socio_del in search_cnpj_socios_del:
                socio_del.unlink()

        if result:
            for socio in result:
                qualificacao = str(socio['qualificacao_socio']['id']) + " - " + socio['qualificacao_socio']['descricao']
                try:
                    self.write(
                       {"cnpj_socios_id": [(0, 0, {
                           "name": socio['nome'],
                           "qualificacao": qualificacao,
                        })]}
                        )
                    _logger.info("Socio incluido")
                except Exception:
                    _logger.warning("Erro ao incluir socio: %s", socio['nome'])

    def define_inscricao_estadual(self, fiscal_info):
        result_ie = fiscal_info[1]

        if result_ie == []:
            self.inscr_est = ''
        else:
            for ie in result_ie:
                if ie['ativo'] == True:
                    if self.state_id.code == ie['estado']['sigla']:
                        self.inscr_est = ie['inscricao_estadual']
                    if self.state_id.code != ie['estado']['sigla']:
                        search_tax_numbers = self.env['state.tax.numbers'].search(
                            [('partner_id', '=', self.id),
                             ('inscr_est', '=', ie['inscricao_estadual'])]
                        )
                        if not search_tax_numbers:
                            search_state = self.env['res.country.state'].search(
                                [('ibge_code', '=', ie['estado']['ibge_id'])])
                            if search_state:
                                try:
                                    incluir_outras_ies = self.write(
                                        {"state_tax_number_ids": [(0, 0, {
                                            "state_id": search_state.id,
                                            "inscr_est": ie['inscricao_estadual']
                                        })]}
                                    )
                                    _logger.info(
                                        "Inscrição estadual adicional incluída.")
                                except Exception:
                                    _logger.warning(
                                        "Erro ao incluir IE Adicional: %s", ie['inscricao_estadual'])
                                # raise ValidationError(
                                # "Erro ao incluir segunda inscrição estadual: %s estado %s", ie['inscricao_estadual'], ie['estado']['sigla'])

    def write(self, vals):
        if "legal_name" in vals:
            if len(vals["legal_name"]) <= 60:
                self.cnpjws_size_legal_name = len(vals["legal_name"])
                self.cnpjws_manual_razao_social = False
            else:
                self.cnpjws_size_legal_name = len(vals["legal_name"])
                self.cnpjws_manual_razao_social = True

        return super().write(vals)
