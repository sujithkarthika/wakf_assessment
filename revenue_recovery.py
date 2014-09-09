from osv import osv
from osv import fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import pooler
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import addons.decimal_precision as dp
import netsvc

class Revenue_Recovery(osv.osv):
    
    _name = 'revenue.recovery'
    
    def action_approve(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Approved",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'approve','follow_up_id':follow_list})
        return True
    
    def action_send(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"RR Send",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'send','follow_up_id':follow_list})
        return True
    
    def action_execute(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"RR Executed",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            if rec.certificate_no and rec.certified_date:
                self.write(cr, uid, ids, {'state':'execute','follow_up_id':follow_list})
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"RR Cancelled",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            if rec.cancel_date:
                self.write(cr, uid, ids, {'state':'cancel','follow_up_id':follow_list})
        return True
    
    _columns = {
                'reg_no':fields.integer('Register No:', size=16, required=False),
                'assess_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null',readonly=False),
                'wakf_district':fields.many2one('wakf.district','District',ondelete='set null',readonly=False),
                'recover_amount':fields.float('Recover Amount', size=16, required=False),
                'collection_charge':fields.float('Collection Charge', size=16, required=False),
                'grand_total':fields.float('Grand Total', size=16, required=False),
                'certified_date':fields.date('Certified Date', required=False),
                'approve':fields.boolean('Approve', required=False),
                'certified_date':fields.date('Certified Date', required=False),
                'file_no':fields.char('File No:', size=16, required=False),
                'requisiton_no':fields.char('Requisition No:', size=16, required=False),
                'certificate_no':fields.char('Certificate No:', size=16, required=False),
                'send':fields.boolean('Send', required=False),
                'rr_execute':fields.boolean('RR Execute', required=False),
                'cancel':fields.boolean('Cancel', required=False),
                'cancel_date':fields.date('Cancel Date', required=False),
                'partner_id':fields.many2one('res.partner','Wakf Name',ondelete='set null',readonly=False),
                'company_id': fields.many2one('res.company', 'Company',size=64, required=False, readonly=False),
                'user_id':fields.char('user id',size=16),
                'company_id': fields.many2one('res.company', 'Company', required=False),
                'follow_up_id':fields.one2many('follow.up.rr','follow_id','Follow Up'),
                'state': fields.selection([
                    ('submitted', 'Created'),
                    ('approve', 'Approved'),
                    ('send', 'RR Send'),
                    ('execute', 'RR Executed'),            
                    ('cancel', 'RR Cancelled'),
                    ],'status', readonly=False),
                }
    _defaults={
        'user_id': lambda obj, cr, uid, context: uid,
        'state':'submitted'
     }
Revenue_Recovery()

class follow_up_rr(osv.osv):
    
    _name = 'follow.up.rr'
    
    _columns = {
               'name':fields.char('Action',readonly=True),
               'who':fields.many2one('res.users','Who',readonly=True),
               'when':fields.char('When',readonly=True), 
               'follow_id':fields.many2one('revenue.recovery','FOLLOW UP'),
                
                
                }
follow_up_rr()
