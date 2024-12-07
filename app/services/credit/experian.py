from app.services.base import BaseService
from app.core.config import settings
from typing import Dict, Any
import base64
import hmac
import hashlib
import time
from datetime import datetime

class ExperianService(BaseService):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.experian.com/v2"
        self.client_id = settings.EXPERIAN_CLIENT_ID
        self.client_secret = settings.EXPERIAN_CLIENT_SECRET
        self._access_token = None
        self._token_expires_at = 0

    async def initialize(self):
        """Initialize service by getting access token"""
        await self._ensure_valid_token()

    async def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if time.time() > self._token_expires_at - 300:  # Refresh if within 5 minutes of expiry
            auth_url = f"{self.base_url}/oauth2/v1/token"
            payload = {
                "grant_type": "client_credentials",
                "scope": "credit_check"
            }
            headers = {
                "Authorization": f"Basic {self._get_basic_auth()}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = await self.make_request(
                "POST",
                auth_url,
                headers=headers,
                data=payload
            )
            
            self._access_token = response["access_token"]
            self._token_expires_at = time.time() + response["expires_in"]

    def _get_basic_auth(self) -> str:
        """Generate Basic Auth string"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(auth_string.encode()).decode()

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique = hmac.new(
            self.client_secret.encode(),
            timestamp.encode(),
            hashlib.sha256
        ).hexdigest()[:8]
        return f"REQ_{timestamp}_{unique}"

    async def check_credit(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform credit check for a customer
        """
        await self._ensure_valid_token()
        
        url = f"{self.base_url}/creditcheck/v1/reports"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "X-Request-Id": self._generate_request_id()
        }
        
        # Prepare the request payload
        payload = {
            "applicant": {
                "name": {
                    "first": customer_data.get("first_name"),
                    "last": customer_data.get("last_name")
                },
                "dateOfBirth": customer_data.get("date_of_birth").isoformat(),
                "addresses": [{
                    "street": customer_data.get("address", {}).get("street"),
                    "city": customer_data.get("address", {}).get("city"),
                    "state": customer_data.get("address", {}).get("state"),
                    "postalCode": customer_data.get("address", {}).get("postal_code"),
                    "country": customer_data.get("address", {}).get("country")
                }],
                "documentNumber": customer_data.get("id_number")
            },
            "permissiblePurpose": "ACCOUNT_REVIEW",
            "requestedAttributes": [
                "CREDIT_SCORE",
                "PAYMENT_HISTORY",
                "ACCOUNT_HISTORY",
                "PUBLIC_RECORDS"
            ]
        }
        
        try:
            credit_report = await self.make_request(
                "POST",
                url,
                headers=headers,
                json=payload
            )
            
            # Process and standardize the credit report
            return self._process_credit_report(credit_report)
            
        except Exception as e:
            self.logger.error(f"Credit check error: {str(e)}")
            return {
                "status": "ERROR",
                "score": None,
                "risk_level": "UNKNOWN",
                "message": str(e)
            }

    def _process_credit_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Process and standardize credit report"""
        try:
            credit_score = report.get("creditScore", {}).get("score")
            
            # Determine status based on credit score
            if credit_score is None:
                status = "ERROR"
                risk_level = "UNKNOWN"
            elif credit_score >= 700:
                status = "POSITIVE"
                risk_level = "LOW"
            elif credit_score >= 600:
                status = "CAUTION"
                risk_level = "MEDIUM"
            else:
                status = "NEGATIVE"
                risk_level = "HIGH"
            
            # Check for derogatory marks
            derogatory_marks = report.get("publicRecords", [])
            if derogatory_marks:
                status = "NEGATIVE"
                risk_level = "HIGH"
            
            return {
                "status": status,
                "score": credit_score,
                "risk_level": risk_level,
                "report_id": report.get("reportId"),
                "derogatory_marks": len(derogatory_marks),
                "accounts": {
                    "total": len(report.get("accounts", [])),
                    "negative": sum(
                        1 for acc in report.get("accounts", [])
                        if acc.get("status") == "negative"
                    )
                },
                "message": f"Credit check completed. Score: {credit_score}, Status: {status}"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing credit report: {str(e)}")
            return {
                "status": "ERROR",
                "score": None,
                "risk_level": "UNKNOWN",
                "message": f"Error processing credit report: {str(e)}"
            }
