from osv import osv
from osv import fields
from tools.translate import _

class sale_order_inherit(osv.osv):
 
 
    #_name = 'customer.inherit.'
    _inherit = 'sale.order'
    
    def on_change_wakf_regno_to_name(self, cr, uid, ids, reg_no, context=None):
        values = {}
        id_res_partner = self.pool.get('res.partner')
        if reg_no:
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                output = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                values = {
                            'partner_id': output,
               
                    }
            else:
                values ={
                            'partner_id': False,
                              }
                
        return {'value' : values}
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}
        regnoof = self.pool.get('res.partner').browse(cr, uid, part, context=context).wakf_reg_no
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        
        val = {
            'registration_no': regnoof,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}
    
    _columns = {
                'partner_id': fields.many2one('res.partner', 'Wakf Name', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, select=True, track_visibility='always'),
                'total_income_saleorder':fields.char('Total Income', size=16, required=False),
                'total_expense_saleorder':fields.char('Total Expense', size=16, required=False),
                'cash_hand_saleorder':fields.char('Cash in Hand', size=16, required=False),
                'assess_year_saleorder':fields.char('Assessment Year', size=16, required=False),
                'cash_bank_saleorder':fields.char('Cash in Bank', size=16, required=False),
                'registration_no':fields.integer('Registration No:', size=16, required=False),
                'state': fields.selection([
            ('draft', 'Draft Assessment'),
            ('sent', 'Assessment Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Assessment Order'),
            ('manual', 'Assessment to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',),
    }
    _defaults = {
        'state': 'draft',
    }
    
sale_order_inherit()

class product_inherit(osv.osv):
    
    _inherit = 'product.product'
    _columns ={
               'income': fields.boolean('Income', help="Specify if the product can be selected in a sales order line."),
               'expense': fields.boolean('Expense', help="Specify if the product can be selected in a sales order line."),
               'active': fields.boolean('Active', help="If unchecked, it will allow you to hide the property without removing it."),
               'percentage_income':fields.float('Exempted %'),
               'deductable': fields.boolean('Wheather Related', help="Specify if the product can be selected in a sales order line."),
               'related_id': fields.many2one('product.product', 'Related Income',domain=[('income', '=', True)] ),             
               'percentage_expense':fields.float('Deducted %'),
               'remarks1':fields.text('Description:',size=164),
                             
               }
    _defaults = {
               'percentage_income':100
                 }
product_inherit()

class product_template_inherit(osv.osv):
    _inherit = "product.template"
  

    _columns = {
                'type': fields.selection([('consu', 'Assessable'),('service','Service')], 'Product Type', required=True),
                
                }
product_template_inherit()