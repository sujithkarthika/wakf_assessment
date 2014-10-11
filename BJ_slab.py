from osv import osv
from osv import fields
from tools.translate import _

class bj_slab(osv.osv):
    _name = 'bj.slab'
    _order = "id desc"
    _columns = {
            'name':fields.char('Ordo'),
            'order_no':fields.char('Order No'),
            'valid_from':fields.date('BJ Slab valid From'),
            'description':fields.text('Other Information'),
            'approved':fields.boolean('Approved'),
            'slab_id':fields.one2many('bj.slab.line','slab_line_id'),
            'user_id':fields.char('user id',size=16),
                }
    _defaults={
        'user_id': lambda obj, cr, uid, context: uid,
     }
    _sql_constraints = [
        ('bj_approved_uniq', 'unique(approved)', 'First remove active BJ Slab'),
    ]

bj_slab()

class bj_slab_line(osv.osv):
    _name = 'bj.slab.line'
    _columns = {
            'name':fields.char('Ordoo'),
            'sl_no':fields.integer('Serial No'),
            'bj_amount_start':fields.float('Net Amount From(Incld)'),
            'bj_amount_end':fields.float('Net Amount To(Excld)'),
            'percentage':fields.float('Percentage of Increment'), 
            'slab_line_id':fields.many2one('bj.slab','Slab ID',ondelete='set null',required=False),           
                }

bj_slab()