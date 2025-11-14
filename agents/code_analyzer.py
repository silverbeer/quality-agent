"""CodeAnalyzerAgent - Analyzes git diffs and identifies code changes.

This agent is responsible for:
1. Fetching and parsing PR diffs from GitHub
2. Identifying changed files, functions, and classes
3. Classifying file types (source, test, config, docs)
4. Assessing complexity and impact of changes
5. Producing structured CodeChange models for downstream agents
"""

import re
from typing import ClassVar, Optional

import httpx
from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from models.analysis import ChangeType, CodeChange, FileType
from models.github import PullRequestWebhookPayload


class DiffParserTool(BaseTool):
    """Tool for parsing git diffs and extracting file changes.

    This tool fetches the PR diff from GitHub and parses it to identify
    changed files and their modifications.
    """

    name: str = "diff_parser"
    description: str = (
        "Fetches and parses git diffs from GitHub to identify changed files, "
        "added/deleted lines, and modification types. Returns structured file change data."
    )

    def _run(self, diff_url: str, github_token: str | None = None) -> dict:
        """Fetch and parse a git diff.

        Args:
            diff_url: URL to the .diff endpoint
            github_token: Optional GitHub token for authentication

        Returns:
            dict: Parsed diff with file changes
        """
        headers = {"Accept": "application/vnd.github.v3.diff"}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        try:
            response = httpx.get(diff_url, headers=headers, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            diff_content = response.text

            # Parse diff into file changes
            files = self._parse_diff_content(diff_content)
            return {
                "success": True,
                "files": files,
                "total_files": len(files),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": [],
            }

    def _parse_diff_content(self, diff_content: str) -> list[dict]:
        """Parse diff content into structured file changes.

        Args:
            diff_content: Raw git diff text

        Returns:
            list[dict]: List of file changes with metadata
        """
        files = []
        current_file = None

        for line in diff_content.split("\n"):
            # New file diff starts with "diff --git"
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)

                # Extract file path: "diff --git a/path/to/file b/path/to/file"
                match = re.search(r"b/(.+)$", line)
                file_path = match.group(1) if match else "unknown"

                current_file = {
                    "file_path": file_path,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "change_type": "modified",
                    "diff_lines": [],
                }

            # Detect new file
            elif line.startswith("new file mode") and current_file:
                current_file["change_type"] = "added"

            # Detect deleted file
            elif line.startswith("deleted file mode") and current_file:
                current_file["change_type"] = "deleted"

            # Detect renamed file
            elif line.startswith("rename from") and current_file:
                current_file["change_type"] = "renamed"

            # Count additions
            elif line.startswith("+") and not line.startswith("+++") and current_file:
                current_file["lines_added"] += 1
                current_file["diff_lines"].append(line)

            # Count deletions
            elif line.startswith("-") and not line.startswith("---") and current_file:
                current_file["lines_deleted"] += 1
                current_file["diff_lines"].append(line)

            # Context lines (for function detection)
            elif (
                current_file
                and line.startswith("@@")
                or (line.startswith(" ") and len(line) > 1)
            ):
                current_file["diff_lines"].append(line)

        # Don't forget the last file
        if current_file:
            files.append(current_file)

        return files


class FunctionDetectorTool(BaseTool):
    """Tool for detecting changed functions and classes in code.

    Analyzes diff lines to identify function and class definitions that were
    added, modified, or deleted.
    """

    name: str = "function_detector"
    description: str = (
        "Analyzes code diff lines to detect changed functions, methods, and classes. "
        "Supports Python, JavaScript, TypeScript, Java, Go, and other languages."
    )

    # Patterns for different languages
    PATTERNS: ClassVar[dict] = {
        "python": {
            "function": r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "class": r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        },
        "javascript": {
            "function": r"^\s*(?:async\s+)?(?:function\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[=:]\s*(?:async\s+)?\(",
            "class": r"^\s*class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)",
        },
        "typescript": {
            "function": r"^\s*(?:async\s+)?(?:function\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[=:]?\s*\(",
            "class": r"^\s*(?:export\s+)?class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)",
        },
        "java": {
            "function": r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "class": r"^\s*(?:public\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        },
        "go": {
            "function": r"^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "class": r"^\s*type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct",
        },
    }

    def _run(self, file_path: str, diff_lines: list[str]) -> dict:
        """Detect functions and classes in diff lines.

        Args:
            file_path: Path to the file
            diff_lines: Lines from the diff

        Returns:
            dict: Detected functions and classes
        """
        language = self._detect_language(file_path)
        patterns = self.PATTERNS.get(language, self.PATTERNS["python"])

        functions = set()
        classes = set()

        for line in diff_lines:
            # Only look at added/modified lines (starting with + or space)
            if not line or line[0] not in ("+", " "):
                continue

            clean_line = line[1:] if line[0] in ("+", "-", " ") else line

            # Check for function definitions
            func_match = re.search(patterns["function"], clean_line)
            if func_match:
                functions.add(func_match.group(1))

            # Check for class definitions
            class_match = re.search(patterns["class"], clean_line)
            if class_match:
                classes.add(class_match.group(1))

        return {
            "functions": sorted(functions),
            "classes": sorted(classes),
            "language": language,
        }

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            str: Language identifier
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".vue": "javascript",  # Vue.js
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        return "python"  # Default


class FileClassifierTool(BaseTool):
    """Tool for classifying file types (source, test, config, docs).

    Determines the purpose and category of changed files.
    """

    name: str = "file_classifier"
    description: str = (
        "Classifies files into categories: source code, tests, configuration, "
        "documentation, or other. Helps prioritize analysis efforts."
    )

    def _run(self, file_path: str) -> dict:
        """Classify a file based on its path and name.

        Args:
            file_path: Path to the file

        Returns:
            dict: File classification
        """
        path_lower = file_path.lower()

        # Test files
        if any(
            indicator in path_lower
            for indicator in ["/test", "/tests", "_test.", "test_", ".test.", ".spec."]
        ):
            return {
                "file_type": FileType.TEST.value,
                "is_test": True,
                "is_source": False,
            }

        # Configuration files
        if any(
            indicator in path_lower
            for indicator in [
                "config",
                "settings",
                ".env",
                "dockerfile",
                "docker-compose",
                ".yaml",
                ".yml",
                ".json",
                ".toml",
                ".ini",
                "pyproject.toml",
                "package.json",
            ]
        ):
            return {
                "file_type": FileType.CONFIG.value,
                "is_test": False,
                "is_source": False,
            }

        # Documentation
        if any(
            indicator in path_lower
            for indicator in [
                "readme",
                ".md",
                "/docs/",
                "/doc/",
                "documentation",
                "changelog",
                "license",
            ]
        ):
            return {
                "file_type": FileType.DOCUMENTATION.value,
                "is_test": False,
                "is_source": False,
            }

        # Source code files
        if any(
            file_path.endswith(ext)
            for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".vue"]
        ):
            return {
                "file_type": FileType.SOURCE.value,
                "is_test": False,
                "is_source": True,
            }

        # Other
        return {
            "file_type": FileType.OTHER.value,
            "is_test": False,
            "is_source": False,
        }


def create_code_analyzer_agent(github_token: str | None = None) -> Agent:
    """Create and configure the CodeAnalyzerAgent.

    Args:
        github_token: Optional GitHub token for API access

    Returns:
        Agent: Configured CrewAI agent
    """
    # Initialize tools
    diff_parser = DiffParserTool()
    function_detector = FunctionDetectorTool()
    file_classifier = FileClassifierTool()

    # Create agent
    agent = Agent(
        role="Code Change Analyzer",
        goal=(
            "Analyze git diffs from pull requests to identify all code changes, "
            "classify file types, detect changed functions and classes, and assess "
            "the complexity and impact of modifications."
        ),
        backstory=(
            "You are an expert software engineer with deep knowledge of multiple "
            "programming languages and code analysis techniques. Your specialty is "
            "reviewing pull requests and identifying what changed, where it changed, "
            "and the potential impact of those changes. You excel at parsing git diffs "
            "and extracting meaningful insights about code modifications."
        ),
        tools=[diff_parser, function_detector, file_classifier],
        verbose=True,
        allow_delegation=False,
    )

    return agent


def create_code_analysis_task(
    agent: Agent,
    webhook_payload: PullRequestWebhookPayload,
    github_token: str | None = None,
) -> Task:
    """Create a task for the CodeAnalyzerAgent.

    Args:
        agent: The CodeAnalyzerAgent
        webhook_payload: GitHub webhook payload with PR info
        github_token: Optional GitHub token

    Returns:
        Task: Configured CrewAI task
    """
    diff_url = webhook_payload.diff_url

    task = Task(
        description=f"""
Analyze the pull request changes and produce a comprehensive list of CodeChange objects.

Pull Request: {webhook_payload.pr_url}
Repository: {webhook_payload.repo_full_name}
PR Number: {webhook_payload.number}
Diff URL: {diff_url}

Instructions:
1. Use the diff_parser tool to fetch and parse the git diff from: {diff_url}
2. For each changed file:
   - Use file_classifier to determine the file type (source, test, config, docs, other)
   - Use function_detector to identify changed functions and classes
   - Assess the complexity impact (low/medium/high) based on:
     * Number of lines changed
     * Number of functions/classes affected
     * File type and importance
3. Create a CodeChange object for each file with:
   - file_path
   - change_type (added, modified, deleted, renamed)
   - file_type (source, test, config, documentation, other)
   - functions_changed (list of function names)
   - classes_changed (list of class names)
   - lines_added, lines_deleted
   - complexity_impact (low, medium, or high)
   - Any notable imports or related files

Focus on identifying source code changes that will need test coverage analysis.
Prioritize accuracy and completeness in your analysis.

Output: Return a structured list of CodeChange data that can be serialized.
""",
        agent=agent,
        expected_output=(
            "A structured JSON-like list of code changes with file paths, change types, "
            "functions/classes changed, line counts, and complexity assessments."
        ),
    )

    return task


class CodeAnalysisInput(BaseModel):
    """Input model for code analysis."""

    webhook_payload: PullRequestWebhookPayload = Field(description="GitHub webhook payload")
    github_token: str | None = Field(default=None, description="GitHub API token")


class CodeAnalysisOutput(BaseModel):
    """Output model for code analysis."""

    code_changes: list[CodeChange] = Field(description="List of identified code changes")
    total_files: int = Field(description="Total number of files changed")
    source_files: int = Field(description="Number of source code files changed")
    test_files: int = Field(description="Number of test files changed")
