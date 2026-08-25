"""
Global registry for Scripture Pipeline resources.

Tracks projects, datasets, and databases in ~/.sp/ for AI context and resource discovery.
"""
import os
import yaml
from pathlib import Path

from llmflow import paths as _paths
from datetime import datetime
from typing import Optional, Dict, List, Any


class ProjectRegistry:
    """Manages project registration."""

    def __init__(self, registry_path: Path):
        self.path = registry_path / "projects"
        self.path.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        name: str,
        path: str,
        description: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Register a project.

        Args:
            name: Project name (unique identifier)
            path: Absolute path to project directory
            description: Optional project description
            **kwargs: Additional metadata
        """
        if not name:
            raise ValueError("name is required")

        # Check for duplicates
        if self.get(name) is not None:
            raise ValueError(f"Project '{name}' is already registered")

        project_data = {
            "name": name,
            "path": path,
            "created": datetime.now().isoformat(),
        }

        if description:
            project_data["description"] = description

        project_data.update(kwargs)

        # Write to YAML file
        yaml_file = self.path / f"{name}.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(project_data, f, default_flow_style=False, allow_unicode=True)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get project by name."""
        yaml_file = self.path / f"{name}.yaml"
        if not yaml_file.exists():
            return None

        with open(yaml_file) as f:
            return yaml.safe_load(f)

    def list(self) -> List[Dict[str, Any]]:
        """List all registered projects."""
        projects = []
        for yaml_file in self.path.glob("*.yaml"):
            with open(yaml_file) as f:
                projects.append(yaml.safe_load(f))
        return projects

    def unregister(self, name: str) -> None:
        """Remove project from registry."""
        yaml_file = self.path / f"{name}.yaml"
        if yaml_file.exists():
            yaml_file.unlink()


class DatasetRegistry:
    """Manages dataset registration."""

    def __init__(self, registry_path: Path):
        self.path = registry_path / "datasets"
        self.path.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        id: str,
        name: str,
        path: str,
        version: str,
        format: str,
        **kwargs
    ) -> None:
        """
        Register a dataset.

        Args:
            id: Dataset ID (unique identifier)
            name: Human-readable dataset name
            path: Absolute path to dataset directory
            version: Dataset version
            format: Data format (xml, csv, json, etc.)
            **kwargs: Additional metadata
        """
        if not id:
            raise ValueError("id is required")

        # Check for duplicates
        if self.get(id) is not None:
            raise ValueError(f"Dataset '{id}' is already registered")

        dataset_data = {
            "id": id,
            "name": name,
            "path": path,
            "version": version,
            "format": format,
            "downloaded": datetime.now().isoformat(),
        }

        dataset_data.update(kwargs)

        # Write to YAML file
        yaml_file = self.path / f"{id}.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(dataset_data, f, default_flow_style=False, allow_unicode=True)

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get dataset by ID."""
        yaml_file = self.path / f"{id}.yaml"
        if not yaml_file.exists():
            return None

        with open(yaml_file) as f:
            return yaml.safe_load(f)

    def exists(self, id: str) -> bool:
        """Check if dataset is registered."""
        return self.get(id) is not None

    def list(self) -> List[Dict[str, Any]]:
        """List all registered datasets."""
        datasets = []
        for yaml_file in self.path.glob("*.yaml"):
            with open(yaml_file) as f:
                datasets.append(yaml.safe_load(f))
        return datasets

    def find(self, **filters) -> List[Dict[str, Any]]:
        """
        Find datasets matching filters.

        Args:
            **filters: Field => value pairs to match

        Returns:
            List of matching datasets
        """
        all_datasets = self.list()
        results = []

        for dataset in all_datasets:
            match = True
            for key, value in filters.items():
                if dataset.get(key) != value:
                    match = False
                    break
            if match:
                results.append(dataset)

        return results

    def unregister(self, id: str) -> None:
        """Remove dataset from registry."""
        yaml_file = self.path / f"{id}.yaml"
        if yaml_file.exists():
            yaml_file.unlink()


class DatabaseRegistry:
    """Manages database registration."""

    def __init__(self, registry_path: Path):
        self.path = registry_path / "databases"
        self.path.mkdir(parents=True, exist_ok=True)
        self.yaml_file = self.path / "databases.yaml"

    def _load(self) -> Dict[str, Any]:
        """Load databases from YAML file."""
        if not self.yaml_file.exists():
            return {"databases": []}

        with open(self.yaml_file) as f:
            return yaml.safe_load(f) or {"databases": []}

    def _save(self, data: Dict[str, Any]) -> None:
        """Save databases to YAML file."""
        with open(self.yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    def register(
        self,
        name: str,
        type: str,
        **kwargs
    ) -> None:
        """
        Register a database.

        Args:
            name: Database name (unique identifier)
            type: Database type (basex, duckdb, etc.)
            **kwargs: Type-specific metadata (host, port, path, etc.)
        """
        if not name:
            raise ValueError("name is required")
        if not type:
            raise ValueError("type is required")

        data = self._load()

        # Check for duplicates
        if any(db["name"] == name for db in data["databases"]):
            raise ValueError(f"Database '{name}' is already registered")

        db_data = {
            "name": name,
            "type": type,
            "loaded": datetime.now().isoformat(),
        }

        db_data.update(kwargs)

        data["databases"].append(db_data)
        self._save(data)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get database by name."""
        data = self._load()
        for db in data["databases"]:
            if db["name"] == name:
                return db
        return None

    def list(self) -> List[Dict[str, Any]]:
        """List all registered databases."""
        data = self._load()
        return data["databases"]

    def find(self, **filters) -> List[Dict[str, Any]]:
        """
        Find databases matching filters.

        Args:
            **filters: Field => value pairs to match

        Returns:
            List of matching databases
        """
        all_databases = self.list()
        results = []

        for db in all_databases:
            match = True
            for key, value in filters.items():
                if db.get(key) != value:
                    match = False
                    break
            if match:
                results.append(db)

        return results

    def unregister(self, name: str) -> None:
        """Remove database from registry."""
        data = self._load()
        data["databases"] = [db for db in data["databases"] if db["name"] != name]
        self._save(data)


class AIContextRegistry:
    """Manages AI context file registration and discovery."""

    def __init__(self, registry_path: Path):
        self.path = registry_path / "ai-context"
        self.path.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        file: str,
        project: str,
        description: str,
        topics: List[str],
        **kwargs
    ) -> None:
        """
        Register an AI context file.

        Args:
            file: Filename (e.g., "basex-patterns.md")
            project: Project name this context belongs to
            description: Brief description of the content
            topics: List of topic tags for searchability
            **kwargs: Additional metadata (e.g., path)
        """
        if not file:
            raise ValueError("file is required")

        # Check for duplicates
        if self.get(file) is not None:
            raise ValueError(f"AI context file '{file}' is already registered")

        context_data = {
            "file": file,
            "project": project,
            "description": description,
            "topics": topics,
            "created": datetime.now().isoformat(),
        }

        context_data.update(kwargs)

        # Write to YAML file (name is filename with .yaml extension)
        yaml_file = self.path / f"{file}.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(context_data, f, default_flow_style=False, allow_unicode=True)

    def get(self, file: str) -> Optional[Dict[str, Any]]:
        """Get AI context file metadata by filename."""
        yaml_file = self.path / f"{file}.yaml"
        if not yaml_file.exists():
            return None

        with open(yaml_file) as f:
            return yaml.safe_load(f)

    def list(self) -> List[Dict[str, Any]]:
        """List all registered AI context files."""
        contexts = []
        for yaml_file in self.path.glob("*.yaml"):
            with open(yaml_file) as f:
                contexts.append(yaml.safe_load(f))
        return contexts

    def search(
        self,
        topic: Optional[str] = None,
        topics: Optional[List[str]] = None,
        project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for AI context files by topic(s) and/or project.

        Args:
            topic: Single topic to search for
            topics: List of topics (matches if ANY topic matches)
            project: Filter by project name

        Returns:
            List of matching AI context file metadata
        """
        all_contexts = self.list()
        results = []

        # Build search topics list
        search_topics = []
        if topic:
            search_topics.append(topic)
        if topics:
            search_topics.extend(topics)

        for context in all_contexts:
            # Check project filter
            if project and context.get("project") != project:
                continue

            # Check topic filter
            if search_topics:
                context_topics = context.get("topics", [])
                # Match if ANY search topic is in context topics
                if not any(t in context_topics for t in search_topics):
                    continue

            results.append(context)

        return results

    def unregister(self, file: str) -> None:
        """Remove AI context file from registry."""
        yaml_file = self.path / f"{file}.yaml"
        if yaml_file.exists():
            yaml_file.unlink()


class Registry:
    """
    Global registry for Scripture Pipeline resources.

    Tracks projects, datasets, and databases in ~/.sp/ directory.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize registry.

        Args:
            registry_path: Override default registry location.
                          If None, uses SP_REGISTRY_PATH env var or ~/.sp/
        """
        if registry_path is None:
            # Check environment variable
            env_path = os.getenv("SP_REGISTRY_PATH")
            if env_path:
                registry_path = Path(env_path)
            else:
                registry_path = _paths.sp_home()

        self.path = Path(registry_path)
        self.path.mkdir(parents=True, exist_ok=True)

        # Initialize sub-registries
        self.projects = ProjectRegistry(self.path)
        self.datasets = DatasetRegistry(self.path)
        self.databases = DatabaseRegistry(self.path)
        self.ai_context = AIContextRegistry(self.path)

    def generate_ai_context(self) -> str:
        """
        Generate formatted context text for AI.

        Returns:
            Formatted string describing all registered resources
        """
        lines = ["Scripture Pipeline Registry", "=" * 40, ""]

        # User context (~/.sp/user-context/*.md) — machine-level instructions
        user_context_dir = self.path / "user-context"
        if user_context_dir.exists():
            md_files = sorted(user_context_dir.glob("*.md"))
            for md_file in md_files:
                try:
                    lines.append(md_file.read_text(encoding="utf-8"))
                    lines.append("")
                except OSError:
                    pass

        # Projects
        projects = self.projects.list()
        if projects:
            lines.append("Registered Projects:")
            for proj in projects:
                desc = f" - {proj.get('description', 'No description')}" if proj.get('description') else ""
                lines.append(f"- {proj['name']} ({proj['path']}){desc}")
            lines.append("")

        # Datasets
        datasets = self.datasets.list()
        if datasets:
            lines.append("Available Datasets:")
            for ds in datasets:
                lines.append(
                    f"- {ds['id']}: {ds['name']} at {ds['path']} "
                    f"(version {ds['version']}, format: {ds['format']})"
                )
            lines.append("")

        # Databases
        databases = self.databases.list()
        if databases:
            lines.append("Available Databases:")
            for db in databases:
                if db['type'] == 'basex':
                    location = f"{db.get('host', 'localhost')}:{db.get('port', 1984)}"
                    lines.append(f"- BaseX collection '{db['name']}' ({location})")
                    if 'source_dataset' in db:
                        lines.append(f"  Source: {db['source_dataset']} dataset")
                elif db['type'] == 'duckdb':
                    lines.append(f"- DuckDB '{db['name']}' at {db.get('path', 'unknown')}")
                else:
                    lines.append(f"- {db['type']} '{db['name']}'")
            lines.append("")

        return "\n".join(lines)
