# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_is_zero

from ...l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    CFOP_DESTINATION_EXTERNAL,
    FINAL_CUSTOMER_NO,
    FINAL_CUSTOMER_YES,
    FISCAL_IN,
    FISCAL_OUT,
    NFE_IND_IE_DEST_1,
    NFE_IND_IE_DEST_2,
    NFE_IND_IE_DEST_9,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    TAX_BASE_TYPE_VALUE,
)
from ...l10n_br_fiscal.constants.icms import (
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_DIFAL_DOUBLE_BASE,
    ICMS_DIFAL_PARTITION,
    ICMS_DIFAL_UNIQUE_BASE,
    ICMS_ORIGIN_TAX_IMPORTED,
    ICMS_SN_CST_WITH_CREDIT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT,
    ICSM_CST_CSOSN_ST_BASE,
)

TAX_DICT_VALUES = {
    "name": False,
    "fiscal_tax_id": False,
    "tax_include": False,
    "tax_withholding": False,
    "tax_domain": False,
    "cst_id": False,
    "cst_code": False,
    "base_type": "percent",
    "base": 0.00,
    "base_reduction": 0.00,
    "percent_amount": 0.00,
    "percent_reduction": 0.00,
    "value_amount": 0.00,
    "uot_id": False,
    "tax_value": 0.00,
    "add_to_base": 0.00,
    "remove_from_base": 0.00,
    "compute_reduction": True,
    "compute_with_tax_value": False,
}


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    # @api.model
    # def _compute_icms(self, tax, taxes_dict, **kwargs):
    #     tax_dict = taxes_dict.get(tax.tax_domain)
    #     partner = kwargs.get("partner")
    #     company = kwargs.get("company")
    #     product = kwargs.get("product")
    #     currency = kwargs.get("currency", company.currency_id)
    #     ncm = kwargs.get("ncm")
    #     nbm = kwargs.get("nbm")
    #     cest = kwargs.get("cest")
    #     operation_line = kwargs.get("operation_line")
    #     cfop = kwargs.get("cfop")
    #     fiscal_operation_type = operation_line.fiscal_operation_type or FISCAL_OUT
    #     ind_final = kwargs.get("ind_final", FINAL_CUSTOMER_NO)

    #     # Get Computed IPI Tax
    #     tax_dict_ipi = taxes_dict.get("ipi", {})

    #     if partner.ind_ie_dest in (NFE_IND_IE_DEST_2, NFE_IND_IE_DEST_9) or (
    #         ind_final == FINAL_CUSTOMER_YES
    #     ):
    #         # Add IPI in ICMS Base
    #         tax_dict["add_to_base"] += tax_dict_ipi.get("tax_value", 0.00)

    #     # Adiciona na base de calculo do ICMS nos casos de entrada de importação
    #     if (
    #         cfop
    #         and cfop.destination == CFOP_DESTINATION_EXPORT
    #         and fiscal_operation_type == FISCAL_IN
    #     ):
    #         tax_dict_ii = taxes_dict.get("ii", {})
    #         tax_dict["add_to_base"] += tax_dict_ii.get("tax_value", 0.00)

    #         # Exclusio Oily 4 linhas abaixo
    #         # tax_dict_pis = taxes_dict.get("pis", {})
    #         # tax_dict["add_to_base"] += tax_dict_pis.get("tax_value", 0.00)

    #         # tax_dict_cofins = taxes_dict.get("cofins", {})
    #         # tax_dict["add_to_base"] += tax_dict_cofins.get("tax_value", 0.00)

    #         tax_dict["add_to_base"] += kwargs.get("ii_customhouse_charges", 0.00)

    #         # Exclusio Oily linhas abaixo
    #         # other_value = kwargs.get("other_value", 0.00)
    #         # tax_dict["remove_from_base"] += sum([other_value])
    #         # other_value = kwargs.get("other_value", 0.00)
    #         # tax_dict["add_to_base"] += sum([other_value])

    #         tax_dict["compute_with_tax_value"] = True

    #     tax_dict.update(self._compute_tax(tax, taxes_dict, **kwargs))

    #     # DIFAL
    #     # TODO
    #     # and operation_line.ind_final == FINAL_CUSTOMER_YES):
    #     if (
    #         cfop
    #         and cfop.destination == CFOP_DESTINATION_EXTERNAL
    #         and operation_line.fiscal_operation_type == FISCAL_OUT
    #         and partner.ind_ie_dest == NFE_IND_IE_DEST_9
    #         and tax_dict.get("tax_value")
    #     ):
    #         tax_icms_difal = company.icms_regulation_id.map_tax_icms_difal(
    #             company, partner, product, ncm, nbm, cest, operation_line
    #         )
    #         tax_icmsfcp_difal = company.icms_regulation_id.map_tax_icmsfcp(
    #             company, partner, product, ncm, nbm, cest, operation_line
    #         )

    #         # Difal - Origin Percent
    #         icms_origin_perc = tax_dict.get("percent_amount")

    #         # Difal - Origin Value
    #         icms_origin_value = tax_dict.get("tax_value")

    #         # Difal - Destination Percent
    #         icms_dest_perc = 0.00
    #         if tax_icms_difal:
    #             icms_dest_perc = tax_icms_difal[0].percent_amount

    #         # Difal - FCP Percent
    #         icmsfcp_perc = 0.00
    #         if tax_icmsfcp_difal:
    #             icmsfcp_perc = tax_icmsfcp_difal[0].percent_amount

    #         # Difal - Base
    #         icms_base = tax_dict.get("base")
    #         difal_icms_base = 0.00

    #         # Difal - ICMS Dest Value
    #         icms_dest_value = currency.round(icms_base * (icms_dest_perc / 100))

    #         if partner.state_id.code in ICMS_DIFAL_UNIQUE_BASE:
    #             difal_icms_base = icms_base

    #         if partner.state_id.code in ICMS_DIFAL_DOUBLE_BASE:
    #             difal_icms_base = currency.round(
    #                 (icms_base - icms_origin_value)
    #                 / (1 - ((icms_dest_perc + icmsfcp_perc) / 100))
    #             )

    #             icms_dest_value = currency.round(
    #                 difal_icms_base * (icms_dest_perc / 100)
    #             )

    #         difal_value = icms_dest_value - icms_origin_value

    #         # Difal - Sharing Percent
    #         date_year = fields.Date.today().year

    #         if date_year >= 2019:
    #             tax_dict.update(ICMS_DIFAL_PARTITION[2019])
    #         else:
    #             if date_year == 2018:
    #                 tax_dict.update(ICMS_DIFAL_PARTITION[2018])
    #             if date_year == 2017:
    #                 tax_dict.update(ICMS_DIFAL_PARTITION[2017])
    #             else:
    #                 tax_dict.update(ICMS_DIFAL_PARTITION[2016])

    #         difal_share_origin = tax_dict.get("difal_origin_perc")

    #         difal_share_dest = tax_dict.get("difal_dest_perc")

    #         difal_origin_value = currency.round(difal_value * difal_share_origin / 100)
    #         difal_dest_value = currency.round(difal_value * difal_share_dest / 100)

    #         tax_dict.update(
    #             {
    #                 "icms_origin_perc": icms_origin_perc,
    #                 "icms_dest_perc": icms_dest_perc,
    #                 "icms_dest_base": difal_icms_base,
    #                 "icms_sharing_percent": difal_share_dest,
    #                 "icms_origin_value": difal_origin_value,
    #                 "icms_dest_value": difal_dest_value,
    #             }
    #         )

    #     return taxes_dict

    @api.model
    def _compute_tax(self, tax, taxes_dict, **kwargs):
        """Generic calculation of Brazilian taxes"""

        company = kwargs.get("company", tax.env.company)
        currency = kwargs.get("currency", company.currency_id)
        operation_line = kwargs.get("operation_line")
        fiscal_operation_type = operation_line.fiscal_operation_type or FISCAL_OUT
        cfop = kwargs.get("cfop")
        tax_dict = taxes_dict.get(tax.tax_domain)
        tax_dict.update(
            {
                "name": tax.name,
                "base_type": tax.tax_base_type,
                "tax_include": tax.tax_group_id.tax_include,
                "tax_withholding": tax.tax_group_id.tax_withholding,
                "fiscal_tax_id": tax.id,
                "tax_domain": tax.tax_domain,
                "percent_reduction": tax.percent_reduction,
                "percent_amount": tax_dict.get("percent_amount", tax.percent_amount),
                "cst_id": tax.cst_from_tax(fiscal_operation_type),
            }
        )

        # Exclusivo
        # if (
        #     cfop
        #     and cfop.destination == CFOP_DESTINATION_EXPORT
        #     and fiscal_operation_type == FISCAL_IN
        # ):
        #     other_value = kwargs.get("other_value", 0.00)
        #     tax_dict["remove_from_base"] += sum([other_value])

        if tax.tax_group_id.base_without_icms:
            # Get Computed ICMS Tax
            tax_dict_icms = taxes_dict.get("icms", {})
            tax_dict["remove_from_base"] += tax_dict_icms.get("tax_value", 0.00)

        # TODO futuramente levar em consideração outros tipos de base de calculo
        if float_is_zero(tax_dict.get("base", 0.00), currency.decimal_places):
            tax_dict = self._compute_tax_base(tax, tax_dict, **kwargs)

        base_amount = tax_dict.get("base", 0.00)

        if tax_dict["base_type"] == "percent":
            tax_dict["tax_value"] = currency.round(
                base_amount * (tax_dict["percent_amount"] / 100)
            )

        if tax_dict["base_type"] in ("quantity", "fixed"):
            tax_dict["tax_value"] = currency.round(
                base_amount * tax_dict["value_amount"]
            )

        return tax_dict