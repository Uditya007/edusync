###############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<https://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GradingAssigment(models.Model):
    _name = 'grading.assignment'
    _description = "Grading Assignment"

    name = fields.Char('Name', required=True)
    course_id = fields.Many2one('op.course', 'Course', required=True)
    subject_id = fields.Many2one('op.subject', string='Subject')
    issued_date = fields.Datetime('Issued Date', required=True)
    assignment_type = fields.Many2one('grading.assignment.type',
                                      string='Assignment Type', required=True)
    faculty_id = fields.Many2one(
        'op.faculty', 'Faculty', default=lambda self: self.env[
            'op.faculty'].search([('user_id', '=', self.env.uid)]),
        required=True)
    point = fields.Float('Points')


class OpAssignment(models.Model):
    _name = "op.assignment"
    _inherit = "mail.thread"
    _description = "Assignment"
    _order = "submission_date DESC"
    _inherits = {"grading.assignment": "grading_assignment_id"}

    batch_id = fields.Many2one('op.batch', 'Batch', required=True)
    marks = fields.Float('Marks', tracking=True)
    description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('publish', 'Published'),
        ('finish', 'Finished'), ('cancel', 'Cancel'),
    ], 'Status', required=True, default='draft', tracking=True)
    submission_date = fields.Datetime('Submission Date', required=True,
                                      tracking=True)
    allocation_ids = fields.Many2many('op.student', string='Allocated To')
    assignment_sub_line = fields.One2many('op.assignment.sub.line',
                                          'assignment_id', 'Submission')
    reviewer = fields.Many2one('op.faculty', 'Reviewer')
    active = fields.Boolean(default=True)
    grading_assignment_id = fields.Many2one('grading.assignment', 'Grading Assignment',
                                            required=True, ondelete="cascade")
    assignment_sub_line_count = fields.Integer(
        'Submissions', compute="_compute_assignment_count_compute")
    courses_subjects = fields.Many2many('op.subject')

    @api.constrains('issued_date', 'submission_date')
    def check_dates(self):
        for record in self:
            issued_date = fields.Date.from_string(record.issued_date)
            submission_date = fields.Date.from_string(record.submission_date)
            if issued_date > submission_date:
                raise ValidationError(_(
                    "Submission Date cannot be set before Issue Date."))

    @api.constrains('marks')
    def _check_marks(self):
        for record in self:
            if record.marks < 0:
                raise ValidationError(_("Marks cannot be negative!"))

    def _compute_assignment_count_compute(self):
        self.assignment_sub_line_count = len(self.assignment_sub_line)

    @api.onchange('course_id')
    def onchange_course(self):
        # Course change resets both the batch and the allocation. The
        # cleared batch triggers `onchange_batch_id` on the next tick
        # (with a False batch → allocation stays empty), so the two
        # side-effects compose safely.
        self.batch_id = False
        self.allocation_ids = [(5, 0, 0)]
        if self.course_id:
            subject_ids = self.env['op.course'].search([
                ('id', '=', self.course_id.id)]).subject_ids
            return {'domain': {'subject_id': [('id', 'in', subject_ids.ids)]}}

    @api.onchange('course_id')
    def onchange_subjects(self):
        for rec in self:
            if rec.course_id:
                rec.courses_subjects = rec.course_id.subject_ids

    @api.onchange('batch_id')
    def onchange_batch_id_populate_allocation(self):
        """Auto-populate `allocation_ids` with every student enrolled
        in the chosen batch. Users can still prune the list manually —
        the assignment editor sees the full roster pre-populated and
        can drop individuals if the work isn't for everyone.

        Reads through `op.student.course` (the enrollment link
        table) rather than `op.student` directly, so students who
        transferred courses or are inactive in this batch don't leak
        in from other batches they've been in.
        """
        if not self.batch_id:
            self.allocation_ids = [(5, 0, 0)]
            return
        enrollments = self.env['op.student.course'].search(
            [('batch_id', '=', self.batch_id.id)]
        )
        self.allocation_ids = [(6, 0, enrollments.mapped('student_id').ids)]

    def act_publish(self):
        self.state = 'publish'
        for rec in self:
            rec._notify_students_new_homework()
        return True

    def _notify_students_new_homework(self):
        for rec in self:
            partners = rec.allocation_ids.mapped('partner_id')
            parent_partners = self.env['res.partner']
            for student in rec.allocation_ids:
                if hasattr(student, 'parent_ids') and student.parent_ids:
                    for parent in student.parent_ids:
                        if parent.name:
                            parent_partners |= parent.name
                        elif parent.user_id and parent.user_id.partner_id:
                            parent_partners |= parent.user_id.partner_id
            all_partners = (partners | parent_partners).filtered(lambda p: p and p.id != self.env.user.partner_id.id)
            if not all_partners:
                continue

            subject_name = rec.subject_id.name if rec.subject_id else 'General'
            sub_date = rec.submission_date.strftime('%d %b %Y, %I:%M %p') if rec.submission_date else 'Not specified'
            body = f"""
                <div style="font-family: Arial, sans-serif;">
                    <h4 style="color: #4F46E5; margin-bottom: 8px;">📚 New Homework Assigned: {rec.name}</h4>
                    <p><strong>Course / Class:</strong> {rec.course_id.name or '-'} ({rec.batch_id.name or '-'})</p>
                    <p><strong>Subject:</strong> {subject_name}</p>
                    <p><strong>Submission Deadline:</strong> <span style="color: #DC2626; font-weight: bold;">{sub_date}</span></p>
                    <p><strong>Total Marks:</strong> {rec.marks}</p>
                    <div style="background-color: #F3F4F6; padding: 12px; border-radius: 6px; margin-top: 10px;">
                        <strong>Instructions:</strong><br/>
                        {rec.description or 'Please review the materials and submit on time.'}
                    </div>
                    <p style="margin-top: 15px;">
                        <a href="/my/assignments" style="background-color: #4F46E5; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            View in Student Portal
                        </a>
                    </p>
                </div>
            """
            try:
                rec.message_subscribe(partner_ids=all_partners.ids)
                rec.message_post(
                    body=body,
                    subject=f"New Homework: {rec.name} ({subject_name})",
                    partner_ids=all_partners.ids,
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                )
            except Exception:
                pass

    def act_finish(self):
        result = self.state = 'finish'
        return result and result or False

    def act_cancel(self):
        self.state = 'cancel'

    def act_set_to_draft(self):
        self.state = 'draft'

    def get_assignment_submissions(self):
        return {
            'name': 'Assignment Submissions',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.assignment.sub.line',
            'domain': [('id', 'in', self.assignment_sub_line.ids)],
            'target': 'current',
        }

    def action_share_whatsapp(self):
        self.ensure_one()
        import urllib.parse
        subject = self.subject_id.name if self.subject_id else 'General'
        sub_date = self.submission_date.strftime('%d %b %Y, %I:%M %p') if self.submission_date else 'Soon'
        msg = f"📚 *EduSync Homework Alert*\n\n*Subject:* {subject}\n*Assignment:* {self.name}\n*Class/Batch:* {self.course_id.name or '-'} ({self.batch_id.name or '-'})\n*Due Date:* {sub_date}\n*Total Marks:* {self.marks}\n\n*Instructions:*\n{self.description or 'Please review the materials and submit on time.'}\n\n👉 *View on Student Portal:* http://localhost:8069/my/assignments"
        url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
