from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_login import current_user
from sqlalchemy import func
from app.models import db, Invoice, Customer, Item, CompanySetting, ActivityLog
from app.setup_manager import get_config
from app.ai_voice_service import AIVoiceService

ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/api/ai')

def get_live_business_context():
    """Compiles real-time accounting and compliance metrics from database."""
    today = date.today()
    
    # Invoices stats
    total_invoices = Invoice.query.count()
    submitted_invoices = Invoice.query.filter_by(status='FBR_Submitted').count()
    pending_invoices = Invoice.query.filter(Invoice.status != 'FBR_Submitted').count()
    
    # Financial metrics
    total_sales = db.session.query(func.sum(Invoice.grand_total)).scalar() or 0.0
    total_tax = db.session.query(func.sum(Invoice.total_sales_tax + Invoice.total_further_tax)).scalar() or 0.0
    
    # Today's metrics
    today_invoices = Invoice.query.filter(func.date(Invoice.invoice_date) == today).all()
    today_count = len(today_invoices)
    today_sales = sum(inv.grand_total for inv in today_invoices)
    today_tax = sum(inv.total_sales_tax + inv.total_further_tax for inv in today_invoices)
    
    # Master records
    total_customers = Customer.query.count()
    total_items = Item.query.count()
    
    # Top customer
    top_buyer = "None recorded"
    if total_invoices > 0:
        top_buyer_res = db.session.query(
            Customer.name, func.sum(Invoice.grand_total)
        ).join(Invoice, Invoice.customer_id == Customer.id)\
         .group_by(Customer.name)\
         .order_by(func.sum(Invoice.grand_total).desc())\
         .first()
        if top_buyer_res:
            top_buyer = f"{top_buyer_res[0]} (PKR {top_buyer_res[1]:,.0f})"
            
    company = CompanySetting.get_settings()
    
    context = f"""
[BUSINESS LIVE DATA]
- Company Name: {company.company_name} (NTN: {company.ntn}, STRN: {company.strn})
- City/Province: {company.city}, {company.province}
- Total Invoices Generated: {total_invoices} (FBR Verified: {submitted_invoices}, Pending/Failed: {pending_invoices})
- Total Sales Recorded: PKR {total_sales:,.2f}
- Total Sales Tax Collected: PKR {total_tax:,.2f}
- Today's Invoices Count: {today_count}
- Today's Sales: PKR {today_sales:,.2f} (Tax: PKR {today_tax:,.2f})
- Top Buying Customer: {top_buyer}
- Total Customers: {total_customers}
- Total Catalog Items / Inventory: {total_items}
- Active Tax Rules: Standard Sales Tax 18%, Further Tax 4% for Unregistered Buyers under SRO 350(I)/2024 & Section 23.
"""
    return context, {
        'total_invoices': total_invoices,
        'submitted_invoices': submitted_invoices,
        'total_sales': total_sales,
        'total_tax': total_tax,
        'today_sales': today_sales,
        'today_count': today_count,
        'top_buyer': top_buyer
    }

@ai_bp.route('/copilot', methods=['POST'])
def copilot_query():
    """Interactive conversational agent for voice & chat requests."""
    data = request.get_json() or {}
    user_query = data.get('query', '').strip()
    history = data.get('history', [])
    
    if not user_query:
        return jsonify({
            'success': False,
            'reply': "Aapne koi sawal nahi pucha. Baraye meherbani boliye ya type karein.",
            'text_to_speak': "Aapne koi sawal nahi pucha."
        })

    cfg = get_config()
    language = data.get('language') or cfg.get('ai_voice', {}).get('language', 'ur-PK')
    api_key = cfg.get('ai_voice', {}).get('api_key', '')

    context_str, metrics = get_live_business_context()

    # Detect action intent (e.g. user says "invoice banao", "report dikhao", etc.)
    q_lower = user_query.lower()
    action = None
    if any(k in q_lower for k in ['create invoice', 'nayi invoice', 'invoice banao', 'bill banao', 'new invoice']):
        action = {'type': 'navigate', 'url': '/invoices/create', 'label': 'Create New Invoice'}
    elif any(k in q_lower for k in ['annexure', 'report', 'sales tax return', 'tax report']):
        action = {'type': 'navigate', 'url': '/reports/annexure-c', 'label': 'Open Annexure-C Report'}
    elif any(k in q_lower for k in ['customers', 'grahak', 'customer list']):
        action = {'type': 'navigate', 'url': '/customers', 'label': 'View Customers'}
    elif any(k in q_lower for k in ['inventory', 'items', 'mal', 'stock']):
        action = {'type': 'navigate', 'url': '/items', 'label': 'View Items Catalog'}
    elif any(k in q_lower for k in ['excel', 'export', 'download data']):
        action = {'type': 'navigate', 'url': '/excel', 'label': 'Export to Excel'}

    # Ask Gemini with history if API key available
    reply = None
    if api_key:
        reply = AIVoiceService.ask_copilot(user_query, context_str, language, api_key, history=history)

    # Smart local personality fallback if Gemini is offline or no key
    if not reply:
        reply = generate_local_accounting_reply(user_query, metrics, language, is_followup=bool(history))

    return jsonify({
        'success': True,
        'reply': reply,
        'text_to_speak': reply,
        'action': action,
        'language': language
    })

def generate_local_accounting_reply(q, metrics, language, is_followup=False):
    """Fallback intelligence rule engine providing accurate live numbers."""
    q_l = q.lower()
    is_urdu = (language == 'ur-PK') or any(k in q_l for k in ['kya', 'kitni', 'kitna', 'hai', 'aaj', 'batao', 'salam', 'adaab'])
    
    prefix = "" if is_followup else "Jee janab! "

    if any(k in q_l for k in ['salam', 'hello', 'hi', 'adaab', 'kon ho', 'who are you']):
        if is_urdu:
            return "Walaikum Assalam! Main Munshi AI hoon — aapka digital FBR sales tax aur billing assistant. Aap mujhse aaj ki sale, tax collection, ya FBR rules ke baray mein puch sakte hain."
        return "Hello! I am Munshi AI, your FBR tax and accounting copilot. Ask me about your sales, tax collected, or any FBR regulation."

    if any(k in q_l for k in ['aaj', 'today', 'daily']):
        if is_urdu:
            return f"{prefix}Aaj kul {metrics['today_count']} invoices bani hain aur total sale PKR {metrics['today_sales']:,.0f} hai."
        return f"Today, {metrics['today_count']} invoices have been issued with total sales of PKR {metrics['today_sales']:,.2f}."

    if any(k in q_l for k in ['tax', 'sales tax', 'further tax', 'fbr']):
        if is_urdu:
            return f"{prefix}Aapka kul sales tax collection PKR {metrics['total_tax']:,.0f} hai. Invoices mein 18% standard aur 4% further tax shamil hai."
        return f"Total sales tax collected is PKR {metrics['total_tax']:,.2f} across all processed invoices."

    if any(k in q_l for k in ['sale', 'total sales', 'kamai', 'revenue']):
        if is_urdu:
            return f"System mein kul sales PKR {metrics['total_sales']:,.0f} record ho chuki hain, jisme {metrics['submitted_invoices']} invoices FBR se tasdeeq shuda hain."
        return f"Total recorded sales amount to PKR {metrics['total_sales']:,.2f} with {metrics['submitted_invoices']} FBR verified invoices."

    if any(k in q_l for k in ['customer', 'buyer', 'grahak']):
        if is_urdu:
            return f"Aapka sabse bara khareedar {metrics['top_buyer']} hai."
        return f"Your top purchasing customer is {metrics['top_buyer']}."

    if any(k in q_l for k in ['sro', '350', 'rule', 'section 23']):
        if is_urdu:
            return "FBR SRO 350(I)/2024 ke mutabiq tamam registered businesses ko digital invoicing lazmi hai, aur ghair-registered buyers par 4% Further Tax lagta hai."
        return "Under SRO 350(I)/2024 and Section 23, digital invoicing is mandatory and unregistered buyers incur a 4% Further Tax."

    if is_urdu:
        return f"Janab, aapke system mein kul {metrics['total_invoices']} invoices aur PKR {metrics['total_sales']:,.0f} ki sales maujood hain. Nayi invoice banane ke liye mujhe bataiye."
    return f"Your system currently has {metrics['total_invoices']} invoices with PKR {metrics['total_sales']:,.2f} in total sales. Let me know if you would like to issue a new invoice or export reports."
