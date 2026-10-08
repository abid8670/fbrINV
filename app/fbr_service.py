import io
import json
import base64
import random
import requests
from datetime import datetime
import qrcode
from app.models import CompanySetting, Invoice

class FBRService:
    @staticmethod
    def clean_tax_number(val):
        if not val:
            return ""
        return str(val).replace("-", "").replace(" ", "").strip()

    @classmethod
    def generate_qr_base64(cls, text_content):
        """Generates a base64 encoded PNG image of the QR Code."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(text_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    @classmethod
    def build_fbr_payload(cls, invoice: Invoice, settings: CompanySetting):
        """Builds standard FBR Digital Invoicing (DI V1.12) JSON Payload."""
        customer = invoice.customer
        
        items_payload = []
        for it in invoice.items:
            items_payload.append({
                "itemCode": it.item_code or f"ITM-{it.id}",
                "itemDescription": it.description,
                "hsCode": it.hs_code.strip() if it.hs_code else "8471.3010",
                "quantity": float(it.quantity),
                "uoM": it.uom or "NOS",
                "unitPrice": round(float(it.unit_price), 2),
                "totalValueOfSupply": round(float(it.value_of_supply), 2),
                "salesTaxRate": round(float(it.sales_tax_rate), 2),
                "salesTaxAmount": round(float(it.sales_tax_amount), 2),
                "furtherTaxRate": round(float(it.further_tax_rate), 2),
                "furtherTaxAmount": round(float(it.further_tax_amount), 2),
                "extraTaxRate": 0.0,
                "extraTaxAmount": 0.0,
                "discount": round(float(it.discount_amount), 2),
                "netAmount": round(float(it.total_amount), 2)
            })

        # Determine Scenario ID based on transaction type
        scenario_id = "SN001"  # Standard local supply
        if invoice.invoice_type == "Debit Note":
            scenario_id = "SN002"
        elif invoice.invoice_type == "Credit Note":
            scenario_id = "SN003"

        payload = {
            "invoiceType": invoice.invoice_type,
            "invoiceNumber": invoice.invoice_number,
            "invoiceDate": invoice.invoice_date.strftime("%Y-%m-%d"),
            "posId": settings.pos_id or "POS-001",
            "branchCode": settings.branch_code or "BR-01",
            "sellerNTN": cls.clean_tax_number(settings.ntn),
            "sellerSTRN": cls.clean_tax_number(settings.strn),
            "sellerBusinessName": settings.company_name,
            "sellerAddress": f"{settings.business_address}, {settings.city}, {settings.province}",
            
            "buyerType": customer.buyer_type,
            "buyerNTN": cls.clean_tax_number(customer.ntn) if customer.buyer_type == "Registered" else "",
            "buyerSTRN": cls.clean_tax_number(customer.strn) if customer.buyer_type == "Registered" else "",
            "buyerCNIC": cls.clean_tax_number(customer.cnic) if customer.buyer_type == "Unregistered" else "",
            "buyerBusinessName": customer.name,
            "buyerAddress": f"{customer.address or ''}, {customer.city or ''}, {customer.province or ''}".strip(", "),
            
            "scenarioId": scenario_id,
            "originalInvoiceNumber": invoice.original_fbr_invoice_number or (invoice.original_invoice.invoice_number if invoice.original_invoice else ""),
            "reasonForIssuance": invoice.reason_for_issuance or "",
            "items": items_payload,
            "totalValueOfSupply": round(float(invoice.total_value_of_supply), 2),
            "totalSalesTax": round(float(invoice.total_sales_tax), 2),
            "totalFurtherTax": round(float(invoice.total_further_tax), 2),
            "totalExtraTax": round(float(invoice.total_extra_tax), 2),
            "totalDiscount": round(float(invoice.total_discount), 2),
            "grandTotal": round(float(invoice.grand_total), 2),
            "paymentMode": invoice.payment_mode or "Cash",
            "remarks": invoice.remarks or ""
        }
        return payload

    @classmethod
    def test_connection(cls, settings: CompanySetting):
        """Tests connectivity and token authentication with FBR / PRAL endpoint."""
        if settings.fbr_environment == "mock":
            return {
                "success": True,
                "message": "Mock Sandbox Active: Test connection succeeded. System is ready to simulate FBR DI transactions."
            }
        
        if not settings.fbr_bearer_token:
            return {
                "success": False,
                "message": "Bearer Token missing! Please enter your PRAL / FBR Bearer Token."
            }

        headers = {
            "Authorization": f"Bearer {settings.fbr_bearer_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # Most FBR / PRAL DI endpoints support ping or GET/OPTIONS or ping check
            test_url = settings.fbr_api_url.strip()
            # If standard post url, attempt an OPTIONS or probe request
            resp = requests.get(test_url, headers=headers, timeout=10)
            if resp.status_code in [200, 405]: # 405 means Method Not Allowed on GET, endpoint is alive and auth reached
                return {
                    "success": True,
                    "message": f"Connection successful! Response Code: {resp.status_code}"
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed (HTTP 401 Unauthorized). Please check your Bearer Token."
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "message": "Access Forbidden (HTTP 403). Your IP may need whitelisting on PRAL DICRM portal."
                }
            else:
                return {
                    "success": False,
                    "message": f"FBR Gateway responded with HTTP {resp.status_code}: {resp.text[:200]}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection failed to {settings.fbr_api_url}: {str(e)}"
            }

    @classmethod
    def submit_invoice(cls, invoice: Invoice, settings: CompanySetting):
        """Submits an invoice to FBR DI API or simulates successful submission in mock mode."""
        payload = cls.build_fbr_payload(invoice, settings)
        payload_json = json.dumps(payload, indent=2)
        invoice.fbr_request_payload = payload_json

        # 1. Mock Environment Handling (Instant realistic testing without blocked network/IP issues)
        if settings.fbr_environment == "mock":
            # Generate realistic 18-digit FBR fiscal invoice number
            timestamp_part = datetime.utcnow().strftime("%Y%m%d%H%M")
            random_part = f"{random.randint(100000, 999999)}"
            simulated_fbr_no = f"FBR-DI-{timestamp_part}-{random_part}"
            
            qr_content = (
                f"FBR-DI|INVOICE:{simulated_fbr_no}|SELLER:{settings.ntn}|"
                f"BUYER:{invoice.customer.ntn or invoice.customer.cnic}|"
                f"DATE:{invoice.invoice_date}|AMOUNT:{invoice.grand_total}|STATUS:VERIFIED"
            )
            qr_base64 = cls.generate_qr_base64(qr_content)

            response_data = {
                "status": "Success",
                "code": "00",
                "message": "Invoice successfully registered and verified with FBR Digital Invoicing System (Mock Mode).",
                "fbrInvoiceNumber": simulated_fbr_no,
                "qrCode": qr_content,
                "timestamp": datetime.utcnow().isoformat()
            }
            response_json = json.dumps(response_data, indent=2)

            invoice.fbr_invoice_number = simulated_fbr_no
            invoice.fbr_status_code = "00"
            invoice.fbr_response_message = response_data["message"]
            invoice.fbr_qr_code_data = qr_content
            invoice.fbr_qr_image_base64 = qr_base64
            invoice.fbr_submitted_at = datetime.utcnow()
            invoice.fbr_response_payload = response_json
            invoice.status = "FBR_Submitted"
            
            return {
                "success": True,
                "fbr_invoice_number": simulated_fbr_no,
                "message": "Invoice verified and submitted to FBR DI (Mock mode)."
            }

        # 2. Live PRAL / FBR Digital Invoicing REST API Call
        if not settings.fbr_bearer_token:
            invoice.status = "Failed"
            invoice.fbr_response_message = "Bearer Token is missing in FBR Settings."
            return {"success": False, "message": invoice.fbr_response_message}

        headers = {
            "Authorization": f"Bearer {settings.fbr_bearer_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            resp = requests.post(
                settings.fbr_api_url.strip(),
                json=payload,
                headers=headers,
                timeout=25
            )
            
            invoice.fbr_submitted_at = datetime.utcnow()
            invoice.fbr_status_code = str(resp.status_code)
            invoice.fbr_response_payload = resp.text

            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {}

            if resp.status_code in [200, 201]:
                # Extract FBR invoice number (accommodating slight variations in PRAL API response schema)
                fbr_no = (
                    resp_json.get("invoiceNumber") or 
                    resp_json.get("fbrInvoiceNumber") or 
                    resp_json.get("fbrInvoiceNo") or 
                    resp_json.get("invoice_id") or
                    f"FBR-{invoice.invoice_number}"
                )
                qr_data = resp_json.get("qrCode") or resp_json.get("qrCodeData") or f"FBR:{fbr_no}"
                qr_base64 = cls.generate_qr_base64(qr_data)

                invoice.fbr_invoice_number = str(fbr_no)
                invoice.fbr_qr_code_data = qr_data
                invoice.fbr_qr_image_base64 = qr_base64
                invoice.fbr_response_message = resp_json.get("message") or "Invoice validated and registered with FBR successfully."
                invoice.status = "FBR_Submitted"

                return {
                    "success": True,
                    "fbr_invoice_number": fbr_no,
                    "message": "Invoice successfully registered with FBR DI System."
                }
            else:
                err_msg = resp_json.get("message") or resp_json.get("errors") or f"FBR Error {resp.status_code}: {resp.text[:300]}"
                invoice.fbr_response_message = str(err_msg)
                invoice.status = "Failed"
                return {
                    "success": False,
                    "message": f"FBR DI API Rejected Invoice: {err_msg}"
                }

        except requests.exceptions.RequestException as e:
            invoice.fbr_response_message = f"Network/Timeout Error connecting to FBR: {str(e)}"
            invoice.status = "Failed"
            return {
                "success": False,
                "message": invoice.fbr_response_message
            }
