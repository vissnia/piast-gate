from fastapi import Depends
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor_factory import DocumentProcessorFactory
from infrastructure.factories.processor_factory import DocumentProcessorFactory as ConcreteDocumentProcessorFactory
from application.use_cases.anonymize_document_use_case import AnonymizeDocumentUseCase
from api.di.chat_container import get_anonymizer_service

def get_document_processor_factory() -> DocumentProcessorFactory:
    """Dependency provider for DocumentProcessorFactory."""
    return ConcreteDocumentProcessorFactory()

def get_anonymize_document_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
    factory: DocumentProcessorFactory = Depends(get_document_processor_factory)
) -> AnonymizeDocumentUseCase:
    """Dependency provider for AnonymizeDocumentUseCase."""
    return AnonymizeDocumentUseCase(anonymizer, factory)
