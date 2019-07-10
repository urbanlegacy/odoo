# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.amazon_odoo_bridge.tools.tools import CHANNELDOMAIN,extract_item
from odoo.addons.amazon_odoo_bridge.tools.tools import FIELDS,MAPPINGDOMAIN,ProductIdType
from odoo.addons.odoo_multi_channel_sale.tools import DomainVals,MapId
from odoo import api,fields, models, _
class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def mws_order_status_update(self):
        for rec in self:
            self.channel_mapping_ids[0].channel_id.mws_order_status_update(rec)

class ProductVariantFeed(models.Model):
    _inherit = "product.variant.feed"
    wk_asin= fields.Char(
        string='ASIN'
    )

class ProductFeed(models.Model):
    _inherit = "product.feed"

    @api.model
    def get_product_fields(self):
        res = super(ProductFeed,self).get_product_fields()
        res+=['wk_asin']
        return res

    wk_asin= fields.Char(
        string='ASIN'
    )

class ProductTemplate(models.Model):
    _inherit = "product.template"

    wk_asin= fields.Char(
        string='ASIN'
    )
    wk_product_id_type = fields.Selection(
        selection_add = [('wk_asin','ASIN')],
    )
    # mws_product_type_id  = fields.Many2one(
    #     comodel_name='mws.product.type',
    #     string='MWS Product Type',
    # )

# class CategoryFeed(models.Model):
#     _inherit = "category.feed"
#
#     @api.model
#     def get_category_fields(self):
#         res = super(CategoryFeed,self).get_category_fields()
#         res+=['mws_product_type_ids','attribute_ids']
#         return res
#
#     mws_product_type_ids  = fields.Text(
#         string='MWS Product Type',
#     )
#     attribute_ids =  fields.Text(
#         comodel_name='product.attribute',
#         string='Attribute',
#     )
#
#     def get_amazon_specific_categ_vals(self,channel_id,vals):
#         amazon_vals = dict()
#
#         mws_product_type = vals.pop('mws_product_type_ids')
#
#         if mws_product_type:
#             mws_product_type_ids = channel_id.mws_import_product_type(
#                 eval(mws_product_type),channel_id)
#             product_type_ids = mws_product_type_ids.get('update_ids')+mws_product_type_ids.get('create_ids')
#             if len(product_type_ids):
#                 amazon_vals['mws_product_type_ids'] = [(6,0,MapId(product_type_ids))]
#
#         attribute = vals.pop('attribute_ids')
#
#         if attribute:
#             attribute_ids = channel_id.mws_import_attributes(
#                 eval(attribute),channel_id).get('create_attr_ids')
#             if len(attribute_ids):
#                 amazon_vals['attribute_ids'] =  [(6,0,MapId(attribute_ids))]
#         vals.update(amazon_vals)
#         return vals
#
# class ProductCategory(models.Model):
#     _inherit = "product.category"
#
#     mws_product_type_ids  = fields.Many2many(
#         comodel_name='mws.product.type',
#         string='MWS Product Type',
#     )
#     attribute_ids =  fields.Many2many(
#         comodel_name='product.attribute',
#         string='Attribute',
#     )

# class MWSProductVariationTheme(models.Model):
#     _name = "mws.product.variation.theme"
#     name = fields.Char()
#     code = fields.Char()
#     channel_id = fields.Many2one(
#         comodel_name='multi.channel.sale',
#         string='Channel',
#         required=1,
#         domain=CHANNELDOMAIN
#     )
#
# class MWSProductType(models.Model):
#     _name = "mws.product.type"
#
#     name = fields.Char()
#     code = fields.Char()
#     channel_id = fields.Many2one(
#         comodel_name='multi.channel.sale',
#         string='Channel',
#         required=1,
#         domain=CHANNELDOMAIN
#     )
#     category_ids = fields.Many2many(
#         comodel_name='product.category',
#         string='Category',
#     )
