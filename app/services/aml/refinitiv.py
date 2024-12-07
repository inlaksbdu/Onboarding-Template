from app.services.base import BaseService
from app.core.config import get_settings
from typing import Dict, Any
import jwt
import time

settings = get_settings()

class RefinitivService(BaseService):
    """
    Refinitiv World-Check One API for AML screening
    Documentation: https://developers.refinitiv.com/en/api-catalog/world-check-one/world-check-one-kyc-api
    """
    
    def init(self):
        super().init()
        self.base_url = "https://api.refinitiv.com"
        self.username = settings.REFINITIV_USERNAME
        self.password = settings.REFINITIV_PASSWORD
        self.app_key = settings.REFINITIV_APP_KEY
        self._access_token = None
        self._token_expires_at = 0
    
    async def initialize(self):
        await self._ensure_valid_token()
    
    async def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if time.time() > self._token_expires_at - 300:  # Refresh if within 5 minutes of expiry
            auth_url = f"{self.base_url}/auth/oauth2/v1/token"
            payload = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
                "scope": "trapi"
            }
            headers = {
                "Accept": "application/json",
                "X-APP-KEY": self.app_key
            }
            
            response = await self.make_request(
                "POST",
                auth_url,
                headers=headers,
                data=payload
            )
            
            self._access_token = response["access_token"]
            self._token_expires_at = time.time() + response["expires_in"]
    
    async def screen_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Screen customer against World-Check One database
        """
        await self._ensure_valid_token()
        
        url = f"{self.base_url}/kyc/v1/screening"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "X-APP-KEY": self.app_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "case": {
                "name": customer_data["name"],
                "dateOfBirth": customer_data["date_of_birth"].isoformat(),
                "nationality": customer_data["nationality"],
                "searchProfile": "KYC_STANDARD",
                "groupId": "DEFAULT"
            }
        }
        
        screening_result = await self.make_request(
            "POST",
            url,
            headers=headers,
            json=payload
        )
        
        # Process and standardize the screening result
        return {
            "status": "CLEARED" if not screening_result.get("matches") else "FLAGGED",
            "risk_level": screening_result.get("riskLevel", "UNKNOWN"),
            "matches": screening_result.get("matches", []),
            "screening_id": screening_result.get("screeningId")
        }

# Utils for risk assessment
def calculate_risk_score(aml_result: Dict[str, Any], credit_result: Dict[str, Any]) -> int:
    """Calculate comprehensive risk score based on various checks"""
    base_score = 100
    
    # AML risk factors
    if aml_result["status"] == "FLAGGED":
        base_score -= 40
        if aml_result.get("risk_level") == "HIGH":
            base_score -= 20
    
    # Credit risk factors
    if credit_result["status"] == "NEGATIVE":
        base_score -= 30
    elif credit_result["status"] == "CAUTION":
        base_score -= 15
    
    return max(0, min(100, base_score))

def determine_risk_level(risk_score: int) -> str:
    """Determine risk level based on risk score"""
    if risk_score >= 80:
        return "LOW"
    elif risk_score >= 60:
        return "MEDIUM"
    else:
        return "HIGH"

def determine_customer_status(
    aml_status: str,
    credit_status: str,
    risk_score: int
) -> CustomerStatus:
    """Determine final customer status based on all checks"""
    if aml_status == "FLAGGED" and risk_score < 50:
        return CustomerStatus.REJECTED
    elif risk_score < 60:
        return CustomerStatus.PENDING
    else:
        return CustomerStatus.ACTIVE