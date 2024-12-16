from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_anthropic.chat_models import ChatAnthropic

from customer.db.repository.custimer_repository import CustomerRepository
from customer.services.customer_service import CustomerService
from customer.services.verification_service import VerificationService
from customer.services.face_verification_service import FaceVerificationService
from ocr.extractor import DocumentOCRProcessor


class Container(containers.DeclarativeContainer):
    """Application IoC container."""

    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=["customer.api.customer_route"]  # Updated path
    )

    customer_repository = providers.Factory(CustomerRepository)

    # Services
    customer_service = providers.Factory(
        CustomerService, customer_repository=customer_repository
    )

    llm = providers.Singleton(
        ChatAnthropic,
        model_name="claude-3-5-sonnet-latest",
        max_tokens_to_sample=4096,
        timeout=60,
    )

    ocr_processor = providers.Factory(DocumentOCRProcessor, llm=llm)

    face_verification_service = providers.Factory(FaceVerificationService)

    verification_service = providers.Factory(
        VerificationService,
        ocr_processor=ocr_processor,
        face_service=face_verification_service,
    )
