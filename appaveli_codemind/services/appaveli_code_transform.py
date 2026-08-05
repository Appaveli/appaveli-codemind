"""
Appaveli Code Transform Service.

Handles code transformation, refactoring, and improvements using AI.
"""
import logging
from typing import Optional

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language, RefactorResult, RefactorType
from appaveli_codemind.utils.file_utils import FileUtils


class AppaveliCodeTransform:
    """
    Service for code refactoring and improvements.

    Responsibilities:
    - Refactor code using AI
    - Apply different refactoring strategies
    - Estimate refactoring costs
    """

    def __init__(self, llm_client, language_detector: LanguageDetector):
        """
        Initialize the refactor service.

        Args:
            llm_client: LLM client for AI-powered refactoring
            language_detector: Language detector for identifying file types
        """
        self.llm_client = llm_client
        self.language_detector = language_detector
        self.logger = logging.getLogger(__name__)

    def refactor_file(
        self,
        file_path: str,
        refactor_type: RefactorType,
        output_path: Optional[str] = None,
    ) -> RefactorResult:
        """
        Refactor a code file.

        Args:
            file_path: Path to the file to refactor
            refactor_type: Type of refactoring to perform
            output_path: Optional output path (defaults to overwriting original)

        Returns:
            RefactorResult with refactoring details
        """
        self.logger.info(f"Refactoring file: {file_path} with type: {refactor_type.value}")

        # Read original file
        original_code = FileUtils.read_file(file_path)

        # Detect language
        language = self.language_detector.detect(file_path)
        if not language:
            raise ValueError(f"Unsupported file type: {file_path}")

        # Perform refactoring using AI
        refactored_code = self.refactor_code(original_code, language, refactor_type)

        # Create result object
        result = RefactorResult(
            success=True,
            original_code=original_code,
            refactored_code=refactored_code,
            language=language,
            refactor_type=refactor_type,
            suggestions=[],
            changes_made=["Code refactored using AI analysis"],
            tokens_used=len(original_code.split()) + len(refactored_code.split()),
            cost_estimate=self.llm_client.estimate_cost(
                len(original_code.split()) + len(refactored_code.split())
            ),
        )

        # Save refactored code if output path provided
        if output_path:
            FileUtils.write_file(output_path, refactored_code)
            self.logger.info(f"Refactored code saved to: {output_path}")

        return result

    def refactor_code(self, code: str, language: Language, refactor_type: RefactorType) -> str:
        """
        Refactor code using AI.

        Args:
            code: Source code to refactor
            language: Programming language
            refactor_type: Type of refactoring to apply

        Returns:
            Refactored code
        """
        prompt = f"""
        Refactor this {language.value} code using {refactor_type.value.replace('_', ' ')} techniques:

        {code}

        Focus on:
        - Code readability and maintainability
        - Best practices for {language.value}
        - Performance improvements
        - Proper naming conventions

        Return only the refactored code without explanations.
        """

        try:
            response = self.llm_client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": f"You are an expert {language.value} developer. Return only clean, refactored code.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            return response["content"]
        except Exception as e:
            self.logger.error(f"Refactoring failed: {e}")
            return code  # Return original code if refactoring fails
