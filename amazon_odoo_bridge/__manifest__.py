# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Amazon Odoo Bridge(AOB)",
  "summary"              :  "Amazon Odoo Bridge extension provides in-depth integration with Odoo and Amazon.",
  "category"             :  "Website",
  "version"              :  "0.1.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Amazon-Odoo-Bridge.html",
  "description"          :  """Amazon Odoo connector
Odoo Amazon bridge
Odoo amazon connector
Connectors
Odoo bridge
Amazon to odoo
Manage orders
Manage products
Import products
Import customers 
Import orders
Ebay to Odoo
Odoo multi-channel bridge
Multi channel connector
Multi platform connector
Multiple platforms bridge
Connect Amazon with odoo
Amazon bridge
Flipkart Bridge
Magento Odoo Bridge
Odoo magento bridge
Woocommerce odoo bridge
Odoo woocommerce bridge
Ebay odoo bridge
Odoo ebay bridge
Multi channel bridge
Prestashop odoo bridge
Odoo prestahop
Akeneo bridge
Marketplace bridge
Multi marketplace connector
Multiple marketplace platform""",
  "live_test_url"        :  "http://odoo.webkul.com:8010/web/login?db=Amazon_Odoo_Bridge",
  "depends"              :  ['odoo_multi_channel_sale'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'wizard/wizard.xml',
                             'wizard/inherits.xml',
                             'views/views.xml',
                             'views/search.xml',
                             'views/inherits.xml',
                             'data/report.xml',
                             'data/data.xml',
                             'data/cron.xml',
                             'views/dashboard_view_inherited.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  200,
  "currency"             :  "EUR",
  "external_dependencies":  {'python': ['mws']},
}