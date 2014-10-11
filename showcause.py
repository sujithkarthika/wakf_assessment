from osv import osv
from osv import fields
from tools.translate import _

class Show_Cause(osv.osv):
 
    _name = 'show.cause'
    _description = 'show.cause'
    _order = "id desc"
    
    def action_send(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'send'})
        return True
    def action_cancel(self, cr, uid, ids, context=None):
        for rec in self.browse(cr,uid,ids):
            reg_no = rec.reg_no
            output = rec.partner_id.id
            ass_year = rec.assessment_year.id
            acc_year = rec.acc_year_from
        search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('wakf_id','=',output),('assess_year','=',ass_year),('acc_year','=',acc_year)])
        if search_ids:
            self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'invoiced'},context=None)
            self.write(cr, uid, ids, {'state':'cancel'})
        else:
            raise osv.except_osv(_('Warning!'), _('Assessment state changed. Cannot process'))
        return True
 
    _columns = {
            'reg_no':fields.integer('Registration Number:', size=64, required=False),
            'partner_id':fields.many2one('res.partner','Wakf Name',ondelete='set null'),
            'notice_no':fields.char('Notice Number',size=32),
            'notice_date':fields.date('Notice Date'),
            'assessment_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null'),
            'acc_year_from':fields.many2one('account.fiscalyear','Account Year From',ondelete='set null'),
            'acc_year_to':fields.many2one('account.fiscalyear','Account Year To',ondelete='set null'),
            'user_id':fields.char('user id',size=16),
            'amount':fields.float('Amount'),
            'state': fields.selection([
                    ('submitted', 'Showcause Approved'),
                    ('send', 'Showcause Send'),
                    ('cancel', 'Showcause Cancelled'),
                    ],'status', readonly=False),
            'company_id': fields.many2one('res.company', 'Company', required=False)
                    }
    _defaults={
        'state':'submitted',
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='show.cause',context=ctx)
     }
Show_Cause()