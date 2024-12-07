from app.services.base import BaseService
from app.core.config import get_settings
import base64
from typing import Dict, Any

settings = get_settings()

class JumioService(BaseService):
    """
    Jumio's Netverify service for ID verification
    Documentation: https://docs.jumio.com/
    """
    
    def init(self):
        super().init()
        self.base_url = "https://netverify.com/api/v4"
        self.api_token = settings.JUMIO_API_TOKEN
        self.api_secret = settings.JUMIO_API_SECRET
        
    async def initialize(self):
        auth_string = f"{self.api_token}:{self.api_secret}"
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(auth_string.encode()).decode()}",
            "User-Agent": f"{settings.PROJECT_NAME}/{settings.VERSION}",
            "Accept": "application/json"
        }
    
    async def create_verification(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a verification transaction"""
        url = f"{self.base_url}/initiateNetverify"
        payload = {
            "customerInternalReference": customer_data["customer_id"],
            "userReference": customer_data["email"],
            "merchantScanReference": f"scan_{customer_data['customer_id']}",
            "callbackUrl": f"{settings.CALLBACK_URL}/jumio-callback",
            "documentTypes": ["PASSPORT", "IDENTITY_CARD", "DRIVING_LICENSE"],
            "enabledFields": ["document_number", "document_type", "date_of_birth", "expiry_date"]
        }
        
        return await self.make_request("POST", url, headers=self.headers, json=payload)
    
    async def retrieve_verification(self, scan_reference: str) -> Dict[str, Any]:
        """Retrieve verification results"""
        url = f"{self.base_url}/scans/{scan_reference}"
        return await self.make_request("GET", url, headers=self.headers)