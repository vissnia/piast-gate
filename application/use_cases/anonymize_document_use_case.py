from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor_factory import DocumentProcessorFactory

class AnonymizeDocumentUseCase:
    """Use case for anonymizing documents."""

    def __init__(self, anonymizer: AnonymizerService, processor_factory: DocumentProcessorFactory):
        self.anonymizer = anonymizer
        self.processor_factory = processor_factory

    async def execute(self, file_content: bytes, content_type: str) -> bytes:
        """
        Anonymizes the uploaded document.

        Args:
            file_content (bytes): The raw file content.
            content_type (str): The MIME type of the file.

        Returns:
            bytes: The anonymized file content.
        
        Raises:
            ValueError: If the content type is unsupported.
        """
        processor = self.processor_factory.get_processor(content_type)
        return processor.process(file_content, self.anonymizer)
