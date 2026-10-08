from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.models import Invoice, CompanySetting, db
from app.excel_service import ExcelService
from app.fbr_service import FBRService
from app.utils import permission_required, log_activity

excel_bp = Blueprint('excel_ops', __name__, url_prefix='/excel')

@excel_bp.route('/')
@login_required
@permission_required('can_export_data')
def index():
    return render_template('excel/import.html')

@excel_bp.route('/template/items')
@login_required
@permission_required('can_export_data')
def template_items():
    stream = ExcelService.generate_item_template()
    return send_file(
        stream,
        as_attachment=True,
        download_name="FBR_Items_Master_Template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@excel_bp.route('/template/invoices')
@login_required
@permission_required('can_export_data')
def template_invoices():
    stream = ExcelService.generate_invoice_template()
    return send_file(
        stream,
        as_attachment=True,
        download_name="FBR_Invoices_Bulk_Upload_Template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@excel_bp.route('/import/items', methods=['POST'])
@login_required
@permission_required('can_manage_items')
def import_items():
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Please select an Excel or CSV file to upload.', 'danger')
        return redirect(url_for('excel_ops.index'))

    res = ExcelService.import_items(file)
    if res.get('success'):
        msg = f"Items Import Complete: {res.get('imported')} new items imported, {res.get('updated')} updated."
        log_activity(f"Imported Items via Excel: {res.get('imported')} created, {res.get('updated')} updated", "Excel")
        flash(msg, 'success')
    else:
        flash(f"Import failed: {res.get('message')}", 'danger')

    return redirect(url_for('items.index'))

@excel_bp.route('/import/invoices', methods=['POST'])
@login_required
@permission_required('can_manage_invoices')
def import_invoices():
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Please select an Excel file to upload.', 'danger')
        return redirect(url_for('excel_ops.index'))

    auto_submit = request.form.get('auto_submit_fbr') == 'yes'

    res = ExcelService.import_invoices(file, user_id=current_user.id)
    if res.get('success'):
        created_count = res.get('invoices_created', 0)
        created_ids = res.get('invoice_ids', [])
        log_activity(f"Imported Invoices via Excel: {created_count} created (Auto-Submit: {auto_submit})", "Excel")

        if auto_submit and created_ids:
            settings = CompanySetting.get_settings()
            invoices = Invoice.query.filter(Invoice.id.in_(created_ids)).all()
            fbr_success = 0
            fbr_failed = 0
            for inv in invoices:
                fbr_res = FBRService.submit_invoice(inv, settings)
                if fbr_res.get('success'):
                    fbr_success += 1
                else:
                    fbr_failed += 1
            db.session.commit()
            flash(
                f"Batch Complete: {created_count} invoices imported from Excel. "
                f"FBR Live Submission: {fbr_success} successfully registered, {fbr_failed} failed.",
                "success" if fbr_failed == 0 else "warning"
            )
        else:
            flash(f"Successfully processed Excel invoices! {created_count} invoices created as Drafts, ready for FBR submission.", 'success')

        return redirect(url_for('invoices.index'))
    else:
        flash(f"Failed to process invoices: {res.get('message')}", 'danger')
        return redirect(url_for('excel_ops.index'))

@excel_bp.route('/export/invoices')
@login_required
@permission_required('can_export_data')
def export_invoices():
    status = request.args.get('status', '').strip()
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    invoices = query.order_by(Invoice.invoice_date.desc()).all()

    stream = ExcelService.export_invoices(invoices)
    log_activity(f"Exported {len(invoices)} Invoices to Excel", "Excel")
    return send_file(
        stream,
        as_attachment=True,
        download_name=f"FBR_Sales_Invoices_Export_{status or 'All'}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
