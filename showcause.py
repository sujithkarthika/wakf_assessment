from osv import osv
from osv import fields

class Show_Cause(osv.osv):
 
    _name = 'show.cause'
    _description = 'show.cause'
    
    def action_send(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'send'})
        return True
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
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
                    }
    _defaults={
        'state':'submitted',
        'user_id': lambda obj, cr, uid, context: uid,
     }
Show_Cause()