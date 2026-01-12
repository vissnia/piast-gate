from domain.services.anonymizer_service import AnonymizerService
from application.dtos.anonymize_request import AnonymizeRequest
from application.dtos.anonymize_response import AnonymizeResponse

class AnonymizeUseCase:
    """Orchestrates the anonymization flow."""

    def __init__(self, anonymizer: AnonymizerService):
        self.anonymizer = anonymizer

    async def execute(self, request: AnonymizeRequest) -> AnonymizeResponse:
        """
        Processes an anonymization request:
        1. Anonymize user text.
        2. Return result.
        """
        anon_text, _ = self.anonymizer.anonymize(request.text)
        
        return AnonymizeResponse(anonymized_text=anon_text)
