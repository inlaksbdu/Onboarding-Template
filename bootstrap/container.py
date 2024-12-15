from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from Customer.db.repository.custimer_repository import CustomerRepository
from Customer.services.customer_service import CustomerService
from Customer.services.verification_service import VerificationService
from persistence.db.models.base import SessionLocal


class Container(containers.DeclarativeContainer):
    """Application IoC container."""

    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "Customer.api.customer_route"  # Updated path
        ]
    )

    # Repositories
    customer_repository = providers.Factory(CustomerRepository)

    # Services
    customer_service = providers.Factory(
        CustomerService, customer_repository=customer_repository
    )

    verification_service = providers.Singleton(VerificationService)
