# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import requests
import binascii
import logging
_logger = logging.getLogger(__name__)
try:
    from mws import MWSError
except Exception as e:
    _logger.error("install mws")

from odoo import api, fields, models, _
from odoo.exceptions import UserError,RedirectWarning, ValidationError
from odoo.addons.amazon_odoo_bridge.tools.tools import extract_item as EI
from odoo.addons.amazon_odoo_bridge.tools.tools import chunks
from odoo.addons.amazon_odoo_bridge.tools.tools import CHANNELDOMAIN


Source = [
	('all', 'All'),
	('order_ids', 'Order ID(s)'),
]
OrderStatus = [
    'Unshipped',
    'PartiallyShipped',
    'Shipped',
    'Pending'
]
SyncStatus = [
    (True,'success'),
    (False,'error')

]


class ImportMwsOrders(models.TransientModel):
    _name = "import.mws.orders"
    _inherit = ['import.orders']


    report_id = fields.Many2one(
        string='Report',
        comodel_name='mws.report',
        domain=[
        ('state','=','receive'),
        ('report_type','in', ['OPEN_LISTINGS_MERCHANT_LISTINGS']),
        ('ml_data','!=',False),
        ('data','!=',False),
        ]
    )
    max_results = fields.Integer(
        string='Max Result',
        default=100
    )
    @api.model
    def default_get(self,fields):
        res=super(ImportMwsOrders,self).default_get(fields)
        context = dict(self._context)
        params =context.get('params',{})
        active_id = context.get('active_id') or params.get('id')
        model = 'multi.channel.sale'
        if (active_id and
            (context.get('active_model')==model or params.get('model')==model)):
            context['channel_id'] = active_id
            report_status = self.channel_id.with_context(context).mws_ensure_report()
            report_id = report_status.get('report_id')
            if report_status.get('message'):
                action_id = self.env.ref('amazon_odoo_bridge.action_reports').id
                raise RedirectWarning(report_status.get('message'), action_id, _('Go to the report panel.'))
        return res

    @api.model
    def _wk_list_orders(self, **kwargs):
        res = {'data': None,'message':''}
        order_vals = self.read(['from_date','to_date'])[0]
        channel_id = self.channel_id
        order = channel_id._get_mws('Orders')

        lastupdatedafter = fields.Datetime.from_string(
            self.from_date).isoformat()
        lastupdatedbefore = fields.Datetime.from_string(
            self.to_date).isoformat()

        try:
            response = order.list_orders(
                marketplaceids = [channel_id.mws_marketplace_id],
                lastupdatedafter = lastupdatedafter,
                lastupdatedbefore = lastupdatedbefore
            )
            res['data'] = response.parsed
        except MWSError as me:
            message = _('MWSError while list orders %s'%(me))
            _logger.error("##%s"%(message))
            res['message'] = message
        except Exception as e:
            message = _('Exception while list orders %s'%(e))
            _logger.error("##%s"%(message))
            res['message'] = message
        return res

    def _wk_order_by_ids(self, order_ids):
        res = {'data': None}

        order = self.channel_id._get_mws('Orders')
        try:
            response = order.get_order(amazon_order_ids = order_ids)
            res['data'] = response.parsed
        except MWSError as me:
            message =_('MWSError while list orders ids [%s]  %s'%(order_ids,me))
            _logger.error("##%s"%(message))
            res['message']=message
        except Exception as e:
            message =_('Exception while list orders ids[%s]  %s'%(order_ids,e))
            _logger.error("##%s"%(message))
            res['message']=message
        return res

    def _wk_list_order_items(self,order_id):
        res = {'data': None}

        order = self.channel_id._get_mws('Orders')
        try:
            response = order.list_order_items(amazon_order_id=order_id)
            res['data'] = response.parsed
        except MWSError as me:
            message =_('MWSError while list orders items [%s]  %s'%(order_id,me))
            _logger.error("##%s"%(message))
            res['message']=message
        except Exception as e:
            message =_('Exception while list orders items[%s]  %s'%(order_id,e))
            _logger.error("##%s"%(message))
            res['message']=message
        return res

    def wk_list_order_items(self,order_id):
        response = self._wk_list_order_items(order_id)
        res_data =  response.get('data',{})
        message = response.get('message','')
        res=None
        if res_data:
            res={}
            OrderItem= res_data.get('OrderItems',{}).get('OrderItem',{})
            if type(OrderItem)!=list:
                OrderItem = [OrderItem]
            for item in OrderItem:
                SellerSKU = EI(item.get('SellerSKU'))
                data =dict(
                    SellerSKU=SellerSKU,
                    Title = EI(item.get('Title')),
                    ASIN = EI(item.get('ASIN')),
                    QuantityOrdered = EI(item.get('QuantityOrdered')),
                    ItemPrice =EI(item.get('ItemPrice',{}).get('Amount')),
                    ShippingPrice =EI(item.get('ShippingPrice',{}).get('Amount','0.0')),
                    ItemTax = EI(item.get('ItemTax',{}).get('Amount')),
                )
                res[SellerSKU]=data
        return dict(
            data = res,
            message =message
            )

    def process_order_data(self,orders):
        if orders:
            if type(orders)!=list:orders=[orders]
            response={}
            for order in filter(lambda order: EI(order.get('OrderStatus')) in OrderStatus ,orders):
                AmazonOrderId = EI(order.get('AmazonOrderId'))
                data = dict(
                    OrderStatus=EI(order.get('OrderStatus')),
                    PurchaseDate = EI(order.get('PurchaseDate',)),
                    BuyerEmail = EI(order.get('BuyerEmail')),
                    BuyerName  = EI(order.get('BuyerName')),
                    PaymentMethod = EI(order.get('PaymentMethod')),
                    FulfillmentChannel =  EI(order.get('FulfillmentChannel')),
                    ShippingAddress = order.get('ShippingAddress'),
                    AmazonOrderId =AmazonOrderId ,
                    OrderTotal = order.get('OrderTotal',{}),
                )
                response[AmazonOrderId]=data
            return response
    def wk_list_orders(self):
        response = self._wk_list_orders()
        orders=[]
        res_data = response.get('data',{})
        if res_data:
            orders = res_data.get('Orders',{}).get('Order',{})
        order_data=self.process_order_data(orders)
        return dict(
            data=order_data,
            message=response.get('message','')
        )


    def wk_order_by_ids(self,order_ids):
        orders=[]
        message=''
        for item in chunks(list(set(order_ids)),50):
            res= self._wk_order_by_ids(item)
            res_data=res.get('data',{})
            if res_data:
                response = res_data.get('Orders',{}).get('Order',{})
                if type(response)!=list:response=[response]
                if type(response)==list:orders+=response
            else:
                message+=res.get('message','')
        order_data=self.process_order_data(orders)
        return dict(
            data=order_data,
            message=message
        )

    @api.model
    def _wk_fetch_orders(self, channel_id,order_ids=None):
        order_data=[]
        message=''
        if  order_ids:
            order_ids = list(set(order_ids.split(',')))
            res = self.wk_order_by_ids(order_ids)
            order_data =res.get('data')
            message += res.get('message','')

        else:
            res = self.wk_list_orders()
            order_data =res.get('data')
            message += res.get('message','')
        return dict(
            data=order_data,
            message=message
            )

    def import_products(self,sku_keys):

        message='For order product imported %s'%(sku_keys)
        mapping_obj = self.env['channel.product.mappings']
        domain = [('default_code', 'in',sku_keys)]
        channel_id = self.channel_id
        mapped = channel_id._match_mapping(mapping_obj,domain).mapped('default_code')
        sku_keys=list(set(sku_keys)-set(mapped))
        message=''
        if len(sku_keys):
            report_id = self.report_id
            if not report_id:
                report_status = channel_id.mws_ensure_report()
                report_id = report_status.get('report_id')
            try:
                import_product_obj=self.env['import.mws.products']
                vals =dict(
                    report_id=report_id.id,
                    source='product_ids',
                    product_ids=','.join(sku_keys),
                    operation='import',
                    channel_id = channel_id.id
                )
                import_product_id=import_product_obj.create(vals)
                import_product_id.import_now()
            except Exception as e:
                message = "Error while  order product import %s"%(e)
        return message
    def update_shipping_info(self,order_items,order_data,price):
        ASIN =order_data.get('FulfillmentChannel','')
        name = 'Amazon%s'%(ASIN)
        order_items[ASIN] = dict(
            QuantityOrdered = 1,
            ASIN =ASIN,
            Title = name,
            ISDelivery =True,
            ItemPrice='%s'%(price),
        )
        return order_items
    def mws_get_tax_line(self,item):
        tax_percent = float(item.get('ItemTax'))
        tax_type = 'fixed'
        name = 'Tax {}'.format(tax_percent)
        return {
            'rate':tax_percent,
            'name':name,
            'tax_type':tax_type
        }
    def get_order_line_feeds(self,order_id,order_data):
        data=dict()
        product_feed_obj = self.env['product.feed']
        res_data = self.wk_list_order_items(order_id)

        order_items=res_data.get('data')
        message=res_data.get('message','')
        lines=[]
        if order_items:
            message+=self.import_products(sku_keys=list(order_items))
            sipping_price=sum(map(lambda item:float(
                item.get('ShippingPrice','0.0')),
                order_items.values()))
            if sipping_price:
                order_items= self.update_shipping_info(
                    order_items,order_data,sipping_price
                )
            size = len(order_items)
            if size==1:
                asin,order_item = order_items.items()[0]

                line=dict(
                    line_product_uom_qty = order_item.get('QuantityOrdered'),
                    # line_product_id = asin,
                    line_product_default_code = order_item.get('SellerSKU'),
                    line_name = order_item.get('Title'),
                    # line_price_unit=order_item.get('ItemPrice')
                    line_price_unit = float(order_item.get('ItemPrice'))/float(order_item.get('QuantityOrdered')),
                )
                if float(order_item.get('ItemTax','0.0').strip()):
                    line['line_taxes'] = [self.mws_get_tax_line(order_item)]
                data.update(line)

            else:
                for asin,order_item in order_items.items():
                    line=dict(
                        line_product_uom_qty = order_item.get('QuantityOrdered'),
                        # line_product_id =asin,
                        line_name = order_item.get('Title'),
                        line_product_default_code = order_item.get('SellerSKU'),
                        # line_price_unit=order_item.get('ItemPrice')
                        line_price_unit = float(order_item.get('ItemPrice'))/float(order_item.get('QuantityOrdered')),

                    )
                    if float(order_item.get('ItemTax','0.0').strip()):
                        line['line_taxes'] = [self.mws_get_tax_line(order_item)]
                    if order_item.get('ISDelivery'):
                        line['line_source']= 'delivery'
                    lines += [(0, 0, line)]
        data['line_ids'] = lines
        data['line_type'] = len(lines) >1 and 'multi' or 'single'
        return dict(
            data=data,
            message=message
            )
    def get_order_vals(self,partner_id,items, order_data):
        pricelist_id = self.channel_id.pricelist_name
        vals=dict(
            partner_id = partner_id,
            payment_method = '%s'%(order_data.get('PaymentMethod','')),
            carrier_id = '%s'%(order_data.get('FulfillmentChannel','')),
            order_state =order_data.get('OrderStatus',''),
            customer_name = order_data.get('BuyerName'),
            customer_email =partner_id,
            invoice_name =order_data.get('BuyerName'),
            invoice_partner_id =partner_id,
            invoice_email =partner_id,
            currency = pricelist_id.currency_id.name,

        )

        addr =  order_data.get('ShippingAddress',{})
        if addr:
            vals['invoice_name'] =EI(addr.get('Name'))
            street = EI(addr.get('AddressLine1'))
            if street:
                vals['invoice_street'] =street
                vals['invoice_street2'] =EI(addr.get('AddressLine2'))
            else:
                vals['invoice_street'] =EI(addr.get('AddressLine2'))
                vals['invoice_street2'] =EI(addr.get('AddressLine3'))

            vals['invoice_phone'] =EI(addr.get('Phone'))
            vals['invoice_city'] =EI(addr.get('City'))
            vals['invoice_zip'] =EI(addr.get('PostalCode'))
            vals['invoice_state_id'] =EI(addr.get('StateOrProvinceCode') or addr.get('StateOrRegion'))
            vals['invoice_country_id'] =EI(addr.get('CountryCode'))

        return vals
    def _update_order_feed(self,mapping,partner_id,line_items, order_data):
        vals = dict()
        order_vals = self.get_order_vals(partner_id,line_items, order_data)
        mapping.write(dict(line_ids=[(5,0,0)]))
        vals.update(line_items)
        vals.update(order_vals)
        vals['state'] =  'update'
        return mapping.write(vals)

    def _mws_create_order_feed(self,partner_id,line_items, order_data,order_id):
        feed_obj = self.env['order.feed']
        vals = self.get_order_vals(partner_id,line_items, order_data)
        vals['store_id']=order_id
        vals.update(line_items)
        return self.channel_id._create_feed(feed_obj, vals)

    def _import_order(self,partner_id,line_items, order_data):
        update =False
        feed_obj =self.env['order.feed']
        mws_order_id =  order_data.get('AmazonOrderId')
        order_obj = self.env['sale.order']
        channel_id =self.channel_id
        match = self.channel_id._match_feed(
            feed_obj, [('store_id', '=',mws_order_id)],limit=1)
        if match:
            update = self._update_order_feed(match,partner_id,
                line_items, order_data)
        else:
            match= self._mws_create_order_feed(
            partner_id,line_items, order_data,mws_order_id)
        return dict(
            feed_id=match,
            update=update
        )
    def import_amazon_orders_status(self,channel_id):
        message = ''
        update_ids = []
        order_state_ids = channel_id.order_state_ids
        default_order_state = order_state_ids.filtered('default_order_state')
        store_order_ids = channel_id.match_order_mappings(
            limit=None).filtered(lambda item:item.order_name.state=='draft'
            ).mapped('store_order_id')
        if not store_order_ids:
            message += 'No order mapping exits'
        else:
            res = self._wk_fetch_orders(
                channel_id=channel_id,
                order_ids =','.join(store_order_ids)
            )
            orders = res.get('data')
            if not orders:
                message = res.get('message','')
                if message:
                    message+=message
                else:
                    message+='No order data received.'

            else:

                for mws_order_id , order_data in orders.items():
                    status = order_data.get('OrderStatus')
                    res = channel_id.set_order_by_status(
                        channel_id= channel_id,
                        store_id = mws_order_id,
                        status = status,
                        order_state_ids = order_state_ids,
                        default_order_state = default_order_state,
                        payment_method =order_data.get('PaymentMethod','')
                    )
                    order_match = res.get('order_match')
                    if order_match:update_ids +=[order_match]
                self._cr.commit()

        time_now = fields.Datetime.now()
        all_imported , all_updated = 1,1
        if all_updated and len(update_ids):
            channel_id.update_order_date = time_now
        if not channel_id.import_order_date:
            channel_id.import_order_date = time_now
        if not channel_id.update_order_date:
            channel_id.update_order_date = time_now
        if channel_id.debug=='enable':
            _logger.info("===%r=%r="%(update_ids,message))
        return dict(
            update_ids=update_ids,
            message = message,
        )
    def import_amazon_orders(self,channel_id):
        create_ids=[]
        update_ids=[]

        order_state_ids = channel_id.order_state_ids
        default_order_state = order_state_ids.filtered('default_order_state')
        feed_obj = self.env['order.feed']
        create_ids = self.env['order.feed']
        update_ids = self.env['order.feed']
        operation = self.operation

        message=''
        res = self._wk_fetch_orders(channel_id=channel_id)
        orders = res.get('data')

        if not orders:
            message = res.get('message','')
            if message:
                message+=message
            else:
                message+='No order data received.'

        else:
            for mws_order_id , order_data in orders.items():
                partner_store_id=order_data.get('BuyerEmail')
                if partner_store_id:
                    match = channel_id._match_feed(
                        feed_obj, [('store_id', '=', mws_order_id),('state','!=','error')])
                    if match and  operation=='import':
                        res = channel_id.set_order_by_status(
                            channel_id= channel_id,
                            store_id = mws_order_id,
                            status = order_data.get('OrderStatus'),
                            order_state_ids = order_state_ids,
                            default_order_state = default_order_state,
                            payment_method =order_data.get('PaymentMethod','')
                        )
                        order_match = res.get('order_match')
                        if order_match:update_ids +=match
                    else:
                        res=self.get_order_line_feeds(mws_order_id,order_data)
                        message+=res.get('message','')
                        line_items = res.get('data')
                        shipping_method =order_data.get('FulfillmentChannel','')
                        if shipping_method:
                            shipping_mapping_id = self.env['shipping.feed'].get_shiping_carrier_mapping(
                            channel_id, shipping_method
                            )
                            line_items['carrier_id']= shipping_mapping_id.shipping_service_id
                        if line_items:
                            import_res=self._import_order(
                                partner_store_id, line_items, order_data)
                            feed_id = import_res.get('feed_id')
                            if import_res.get('update'):
                                update_ids+=feed_id
                            else:
                                create_ids+=feed_id
        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
        )
    @api.multi
    def import_now(self):
        create_ids,update_ids,map_create_ids,map_update_ids=[],[],[],[]
        message=''
        for record in self:
            channel_id = record.channel_id
            feed_res=record.import_amazon_orders(channel_id)

            post_res = self.post_feed_import_process(channel_id,feed_res)
            create_ids+=post_res.get('create_ids')
            update_ids+=post_res.get('update_ids')
            map_create_ids+=post_res.get('map_create_ids')
            map_update_ids+=post_res.get('map_update_ids')
            if len(create_ids):channel_id.set_channel_date('import','order')
            if len(update_ids):channel_id.set_channel_date('update','order')
        message+=self.env['multi.channel.sale'].get_feed_import_message(
            'order',create_ids,update_ids,map_create_ids,map_update_ids
        )
        _logger.info("Import Order===%r=%r= %r"%(update_ids,update_ids,message))
        return self.env['multi.channel.sale'].display_message(message)
    @api.model
    def _cron_mws_import_order(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            channel_id = channel_id
            message = ''
            import_res = None
            report_status = channel_id.mws_ensure_report()
            message+= report_status.get('message')
            report_id = report_status.get('report_id')
            if report_id:
                obj=self.create(dict(report_id=report_id.id,channel_id=channel_id.id))
                obj.import_now()
            if channel_id.debug=='enable':
                _logger.info("message %r=import_res==%r=="%(message,import_res))

    @api.model
    def _cron_mws_import_order_status(self):
        for channel_id in self.env['multi.channel.sale'].search(CHANNELDOMAIN):
            message = ''
            import_res = None
            channel_id = channel_id
            report_status = channel_id.mws_ensure_report()
            message+= report_status.get('message')
            report_id = report_status.get('report_id')
            if report_id:
                obj=self.create(dict(
                    report_id=report_id.id,
                    channel_id=channel_id.id)
                )
                import_res = obj.import_amazon_orders_status(channel_id)
            if channel_id.debug=='enable':
                _logger.info("message %r=import_res==%r=="%(message,import_res))
