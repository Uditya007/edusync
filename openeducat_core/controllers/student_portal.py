###############################################################################
#
#    EduSync ERP - Student & Parent Portal Extensions
#
###############################################################################

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class EduSyncStudentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        if 'timetable_count' in counters:
            values['timetable_count'] = request.env['op.session'].sudo().search_count([]) if student else 0
        if 'assignment_count' in counters:
            values['assignment_count'] = request.env['op.assignment'].sudo().search_count([]) if student else 0
        if 'exam_count' in counters:
            values['exam_count'] = request.env['op.exam'].sudo().search_count([]) if student else 0
        if 'attendance_count' in counters:
            values['attendance_count'] = request.env['op.attendance.line'].sudo().search_count([('student_id', '=', student.id)]) if student else 0
        return values

    @http.route(['/my/timetable'], type='http', auth='user', website=True)
    def portal_my_timetable(self, **kw):
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        sessions = request.env['op.session'].sudo().search([], order='start_datetime desc', limit=50)
        values = {
            'student': student,
            'sessions': sessions,
            'page_name': 'timetable',
        }
        return request.render('openeducat_core.portal_my_timetable', values)

    @http.route(['/my/assignments'], type='http', auth='user', website=True)
    def portal_my_assignments(self, **kw):
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        assignments = request.env['op.assignment'].sudo().search([], order='submission_date desc', limit=50)
        submissions = {}
        if student:
            for sub in request.env['op.assignment.sub.line'].sudo().search([('student_id', '=', student.id)]):
                submissions[sub.assignment_id.id] = sub

        values = {
            'student': student,
            'assignments': assignments,
            'submissions': submissions,
            'page_name': 'assignments',
        }
        return request.render('openeducat_core.portal_my_assignments', values)

    @http.route(['/my/exams'], type='http', auth='user', website=True)
    def portal_my_exams(self, **kw):
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        exams = request.env['op.exam'].sudo().search([], order='start_time desc', limit=50)
        results = request.env['op.result.line'].sudo().search([('student_id', '=', student.id)]) if student else []
        values = {
            'student': student,
            'exams': exams,
            'results': results,
            'page_name': 'exams',
        }
        return request.render('openeducat_core.portal_my_exams', values)

    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_my_attendance(self, **kw):
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        attendances = request.env['op.attendance.line'].sudo().search([('student_id', '=', student.id)], order='attendance_date desc', limit=50) if student else []
        values = {
            'student': student,
            'attendances': attendances,
            'page_name': 'attendance',
        }
        return request.render('openeducat_core.portal_my_attendance', values)

    @http.route(['/my/transport'], type='http', auth='user', website=True)
    def portal_my_transport(self, **kw):
        user = request.env.user
        student = request.env['op.student'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
        if not student and getattr(user, 'is_parent', False):
            parent = request.env['op.parent'].sudo().search([('user_id', '=', user.id)], limit=1)
            if parent and parent.student_ids:
                student = parent.student_ids[0]

        registration = request.env['op.transport.registration'].sudo().search([('student_id', '=', student.id), ('status', '=', 'active')], limit=1) if student else False
        bus = registration.bus_id if registration else False
        all_buses = request.env['op.transport.bus'].sudo().search([])
        values = {
            'student': student,
            'registration': registration,
            'bus': bus,
            'all_buses': all_buses,
            'page_name': 'transport',
        }
        return request.render('openeducat_core.portal_my_transport', values)
