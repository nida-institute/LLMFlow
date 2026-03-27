"""
Tests for the global registry system (~/.sp/).

Following TDD: write tests first, then implement registry.py to make them pass.
"""
import pytest
import yaml
from pathlib import Path
from datetime import datetime
from llmflow.registry import Registry, ProjectRegistry, DatasetRegistry, DatabaseRegistry, AIContextRegistry


class TestRegistryInitialization:
    """Test registry initialization and file structure."""

    def test_registry_creates_directory(self, tmp_path, monkeypatch):
        """Registry should create ~/.sp/ directory if it doesn't exist."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))

        registry = Registry()

        assert registry_path.exists()
        assert registry_path.is_dir()

    def test_registry_creates_subdirectories(self, tmp_path, monkeypatch):
        """Registry should create projects/, datasets/, databases/, ai-context/ subdirs."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))

        registry = Registry()

        assert (registry_path / "projects").exists()
        assert (registry_path / "datasets").exists()
        assert (registry_path / "databases").exists()
        assert (registry_path / "ai-context").exists()

    def test_registry_uses_home_by_default(self, monkeypatch):
        """Registry should default to ~/.sp/ if no env var set."""
        # Don't actually create in real home dir, just verify path logic
        monkeypatch.delenv("SP_REGISTRY_PATH", raising=False)

        registry = Registry()

        assert str(registry.path).endswith(".sp")
        assert registry.path.parent == Path.home()

    def test_registry_respects_env_override(self, tmp_path, monkeypatch):
        """Registry should use SP_REGISTRY_PATH env var if set."""
        custom_path = tmp_path / "custom_registry"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(custom_path))

        registry = Registry()

        assert registry.path == custom_path


class TestProjectRegistry:
    """Test project registration and retrieval."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_register_project(self, registry):
        """Should register a project with metadata."""
        registry.projects.register(
            name="mark-discourse",
            path="/Users/test/projects/mark-discourse",
            description="Discourse analysis of Mark"
        )

        projects = registry.projects.list()
        assert len(projects) == 1
        assert projects[0]["name"] == "mark-discourse"
        assert projects[0]["description"] == "Discourse analysis of Mark"

    def test_get_project_by_name(self, registry):
        """Should retrieve project by name."""
        registry.projects.register(
            name="mark-discourse",
            path="/Users/test/projects/mark-discourse"
        )

        project = registry.projects.get("mark-discourse")

        assert project is not None
        assert project["name"] == "mark-discourse"
        assert project["path"] == "/Users/test/projects/mark-discourse"

    def test_project_persists_across_instances(self, registry, tmp_path, monkeypatch):
        """Registered project should persist to disk."""
        registry.projects.register(
            name="test-project",
            path="/Users/test/projects/test"
        )

        # Create new registry instance
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        new_registry = Registry()

        project = new_registry.projects.get("test-project")
        assert project is not None
        assert project["name"] == "test-project"

    def test_project_includes_timestamp(self, registry):
        """Project registration should include created timestamp."""
        registry.projects.register(
            name="test-project",
            path="/Users/test/projects/test"
        )

        project = registry.projects.get("test-project")

        assert "created" in project
        # Should be ISO 8601 format
        datetime.fromisoformat(project["created"])

    def test_list_projects_returns_all(self, registry):
        """list() should return all registered projects."""
        registry.projects.register(name="proj1", path="/path1")
        registry.projects.register(name="proj2", path="/path2")
        registry.projects.register(name="proj3", path="/path3")

        projects = registry.projects.list()

        assert len(projects) == 3
        names = [p["name"] for p in projects]
        assert "proj1" in names
        assert "proj2" in names
        assert "proj3" in names

    def test_get_nonexistent_project_returns_none(self, registry):
        """get() should return None for nonexistent project."""
        project = registry.projects.get("nonexistent")

        assert project is None

    def test_unregister_project(self, registry):
        """Should remove project from registry."""
        registry.projects.register(name="test", path="/path")

        registry.projects.unregister("test")

        project = registry.projects.get("test")
        assert project is None


class TestDatasetRegistry:
    """Test dataset registration and retrieval."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_register_dataset(self, registry):
        """Should register a dataset with metadata."""
        registry.datasets.register(
            id="macula-greek-lowfat",
            name="Macula Greek Lowfat Syntax Trees",
            path="/Users/test/datasets/macula-greek/lowfat",
            version="2024-12-15",
            format="xml"
        )

        datasets = registry.datasets.list()
        assert len(datasets) == 1
        assert datasets[0]["id"] == "macula-greek-lowfat"
        assert datasets[0]["format"] == "xml"

    def test_get_dataset_by_id(self, registry):
        """Should retrieve dataset by ID."""
        registry.datasets.register(
            id="byzantine-text",
            name="Byzantine Text",
            path="/Users/test/datasets/byzantine",
            version="RP2018",
            format="csv"
        )

        dataset = registry.datasets.get("byzantine-text")

        assert dataset is not None
        assert dataset["id"] == "byzantine-text"
        assert dataset["version"] == "RP2018"

    def test_dataset_exists_check(self, registry):
        """exists() should check if dataset is registered."""
        registry.datasets.register(
            id="test-dataset",
            name="Test",
            path="/path",
            version="1.0",
            format="json"
        )

        assert registry.datasets.exists("test-dataset") is True
        assert registry.datasets.exists("nonexistent") is False

    def test_find_datasets_by_format(self, registry):
        """find() should filter datasets by format."""
        registry.datasets.register(
            id="ds1", name="Dataset 1", path="/p1", version="1.0", format="xml"
        )
        registry.datasets.register(
            id="ds2", name="Dataset 2", path="/p2", version="1.0", format="csv"
        )
        registry.datasets.register(
            id="ds3", name="Dataset 3", path="/p3", version="1.0", format="xml"
        )

        xml_datasets = registry.datasets.find(format="xml")

        assert len(xml_datasets) == 2
        ids = [d["id"] for d in xml_datasets]
        assert "ds1" in ids
        assert "ds3" in ids
        assert "ds2" not in ids

    def test_dataset_includes_downloaded_timestamp(self, registry):
        """Dataset registration should include downloaded timestamp."""
        registry.datasets.register(
            id="test", name="Test", path="/path", version="1.0", format="json"
        )

        dataset = registry.datasets.get("test")

        assert "downloaded" in dataset
        datetime.fromisoformat(dataset["downloaded"])


class TestDatabaseRegistry:
    """Test database registration and retrieval."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_register_basex_collection(self, registry):
        """Should register a BaseX collection."""
        registry.databases.register(
            name="macula-greek",
            type="basex",
            host="localhost",
            port=1984,
            source_dataset="macula-greek-lowfat"
        )

        databases = registry.databases.list()
        assert len(databases) == 1
        assert databases[0]["name"] == "macula-greek"
        assert databases[0]["type"] == "basex"
        assert databases[0]["port"] == 1984

    def test_register_duckdb_file(self, registry):
        """Should register a DuckDB database file."""
        registry.databases.register(
            name="vocab",
            type="duckdb",
            path="/Users/test/projects/vocab.duckdb"
        )

        db = registry.databases.get("vocab")

        assert db is not None
        assert db["type"] == "duckdb"
        assert db["path"] == "/Users/test/projects/vocab.duckdb"

    def test_find_databases_by_type(self, registry):
        """find() should filter databases by type."""
        registry.databases.register(
            name="basex1", type="basex", host="localhost", port=1984
        )
        registry.databases.register(
            name="duck1", type="duckdb", path="/path1.duckdb"
        )
        registry.databases.register(
            name="basex2", type="basex", host="localhost", port=1985
        )

        basex_dbs = registry.databases.find(type="basex")

        assert len(basex_dbs) == 2
        names = [db["name"] for db in basex_dbs]
        assert "basex1" in names
        assert "basex2" in names
        assert "duck1" not in names

    def test_database_includes_loaded_timestamp(self, registry):
        """Database registration should include loaded timestamp."""
        registry.databases.register(
            name="test", type="duckdb", path="/path.duckdb"
        )

        db = registry.databases.get("test")

        assert "loaded" in db
        datetime.fromisoformat(db["loaded"])


class TestRegistryYAMLFormat:
    """Test YAML file format and structure."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_project_yaml_structure(self, registry):
        """Project YAML should have correct structure."""
        registry.projects.register(
            name="test-project",
            path="/Users/test/projects/test",
            description="Test project"
        )

        # Read the YAML file directly
        yaml_file = registry.path / "projects" / "test-project.yaml"
        assert yaml_file.exists()

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert data["name"] == "test-project"
        assert data["path"] == "/Users/test/projects/test"
        assert data["description"] == "Test project"
        assert "created" in data

    def test_dataset_yaml_structure(self, registry):
        """Dataset YAML should have correct structure."""
        registry.datasets.register(
            id="test-dataset",
            name="Test Dataset",
            path="/path/to/dataset",
            version="1.0",
            format="xml"
        )

        yaml_file = registry.path / "datasets" / "test-dataset.yaml"
        assert yaml_file.exists()

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert data["id"] == "test-dataset"
        assert data["name"] == "Test Dataset"
        assert data["version"] == "1.0"
        assert data["format"] == "xml"
        assert "downloaded" in data

    def test_databases_yaml_grouped(self, registry):
        """All databases should be in single databases.yaml file."""
        registry.databases.register(
            name="db1", type="basex", host="localhost", port=1984
        )
        registry.databases.register(
            name="db2", type="duckdb", path="/path.duckdb"
        )

        yaml_file = registry.path / "databases" / "databases.yaml"
        assert yaml_file.exists()

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert "databases" in data
        assert len(data["databases"]) == 2


class TestRegistryValidation:
    """Test registry validation and error handling."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_register_project_empty_name(self, registry):
        """Should raise error if name is empty."""
        with pytest.raises(ValueError, match="name.*required"):
            registry.projects.register(name="", path="/path")

    def test_register_dataset_empty_id(self, registry):
        """Should raise error if id is empty."""
        with pytest.raises(ValueError, match="id.*required"):
            registry.datasets.register(
                id="", name="Test", path="/path", version="1.0", format="xml"
            )

    def test_duplicate_project_name_raises_error(self, registry):
        """Registering duplicate project name should raise error."""
        registry.projects.register(name="test", path="/path1")

        with pytest.raises(ValueError, match="already registered"):
            registry.projects.register(name="test", path="/path2")

    def test_duplicate_dataset_id_raises_error(self, registry):
        """Registering duplicate dataset ID should raise error."""
        registry.datasets.register(
            id="test", name="Test 1", path="/p1", version="1.0", format="xml"
        )

        with pytest.raises(ValueError, match="already registered"):
            registry.datasets.register(
                id="test", name="Test 2", path="/p2", version="1.0", format="csv"
            )


class TestRegistryContextForAI:
    """Test AI context generation from registry."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry with sample data."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        reg = Registry()

        # Register some sample data
        reg.projects.register(
            name="mark-discourse",
            path="/Users/test/projects/mark-discourse",
            description="Discourse analysis of Mark"
        )
        reg.datasets.register(
            id="macula-greek-lowfat",
            name="Macula Greek Lowfat",
            path="/Users/test/datasets/macula-greek/lowfat",
            version="2024-12-15",
            format="xml"
        )
        reg.databases.register(
            name="macula-greek",
            type="basex",
            host="localhost",
            port=1984,
            source_dataset="macula-greek-lowfat"
        )

        return reg

    def test_generate_ai_context(self, registry):
        """Should generate formatted context text for AI."""
        context = registry.generate_ai_context()

        assert "Scripture Pipeline Registry" in context
        assert "mark-discourse" in context
        assert "macula-greek-lowfat" in context
        assert "BaseX collection" in context or "basex" in context.lower()

    def test_ai_context_includes_paths(self, registry):
        """AI context should include resource paths."""
        context = registry.generate_ai_context()

        assert "/Users/test/datasets/macula-greek/lowfat" in context

    def test_ai_context_includes_metadata(self, registry):
        """AI context should include useful metadata."""
        context = registry.generate_ai_context()

        assert "2024-12-15" in context  # version
        assert "xml" in context  # format
        assert "localhost:1984" in context or "localhost" in context  # host


class TestAIContextRegistry:
    """Test AI context file registration and search."""

    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a test registry."""
        registry_path = tmp_path / ".sp"
        monkeypatch.setenv("SP_REGISTRY_PATH", str(registry_path))
        return Registry()

    def test_register_ai_context_file(self, registry):
        """Should register an AI context file with metadata."""
        registry.ai_context.register(
            file="basex-patterns.md",
            project="mark-discourse",
            description="XQuery examples for Greek syntax trees",
            topics=["basex", "xquery", "greek", "syntax"]
        )

        contexts = registry.ai_context.list()
        assert len(contexts) == 1
        assert contexts[0]["file"] == "basex-patterns.md"
        assert contexts[0]["project"] == "mark-discourse"
        assert contexts[0]["description"] == "XQuery examples for Greek syntax trees"
        assert set(contexts[0]["topics"]) == {"basex", "xquery", "greek", "syntax"}

    def test_get_ai_context_by_file(self, registry):
        """Should retrieve AI context by filename."""
        registry.ai_context.register(
            file="basex-patterns.md",
            project="mark-discourse",
            description="XQuery examples",
            topics=["basex", "xquery"]
        )

        context = registry.ai_context.get("basex-patterns.md")

        assert context is not None
        assert context["file"] == "basex-patterns.md"
        assert context["project"] == "mark-discourse"

    def test_search_ai_context_by_single_topic(self, registry):
        """Should find AI context files by topic."""
        registry.ai_context.register(
            file="basex-patterns.md",
            project="mark-discourse",
            description="XQuery examples",
            topics=["basex", "xquery", "greek"]
        )
        registry.ai_context.register(
            file="duckdb-patterns.md",
            project="mark-discourse",
            description="SQL examples",
            topics=["duckdb", "sql", "vocabulary"]
        )

        results = registry.ai_context.search(topic="basex")

        assert len(results) == 1
        assert results[0]["file"] == "basex-patterns.md"

    def test_search_ai_context_by_multiple_topics(self, registry):
        """Should find AI context files matching any of multiple topics."""
        registry.ai_context.register(
            file="basex-patterns.md",
            project="mark-discourse",
            description="XQuery examples",
            topics=["basex", "xquery", "greek"]
        )
        registry.ai_context.register(
            file="greek-exegesis.md",
            project="mark-discourse",
            description="Greek exegesis patterns",
            topics=["greek", "exegesis", "discourse"]
        )
        registry.ai_context.register(
            file="duckdb-patterns.md",
            project="mark-discourse",
            description="SQL examples",
            topics=["duckdb", "sql"]
        )

        # Search for files with "greek" OR "sql"
        results = registry.ai_context.search(topics=["greek", "sql"])

        assert len(results) == 3
        filenames = [r["file"] for r in results]
        assert "basex-patterns.md" in filenames
        assert "greek-exegesis.md" in filenames
        assert "duckdb-patterns.md" in filenames

    def test_search_ai_context_by_project(self, registry):
        """Should filter AI context files by project."""
        registry.ai_context.register(
            file="basex-patterns.md",
            project="mark-discourse",
            description="XQuery examples",
            topics=["basex"]
        )
        registry.ai_context.register(
            file="hebrew-patterns.md",
            project="genesis-discourse",
            description="Hebrew patterns",
            topics=["hebrew"]
        )

        results = registry.ai_context.search(project="mark-discourse")

        assert len(results) == 1
        assert results[0]["file"] == "basex-patterns.md"

    def test_ai_context_includes_created_timestamp(self, registry):
        """AI context should include creation timestamp."""
        registry.ai_context.register(
            file="test.md",
            project="test-project",
            description="Test file",
            topics=["test"]
        )

        context = registry.ai_context.get("test.md")

        assert "created" in context
        datetime.fromisoformat(context["created"])

    def test_ai_context_yaml_structure(self, registry):
        """AI context YAML should have correct structure."""
        registry.ai_context.register(
            file="test.md",
            project="test-project",
            description="Test description",
            topics=["topic1", "topic2"],
            path="/full/path/to/test.md"  # Optional
        )

        yaml_file = registry.path / "ai-context" / "test.md.yaml"
        assert yaml_file.exists()

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert data["file"] == "test.md"
        assert data["project"] == "test-project"
        assert data["description"] == "Test description"
        assert data["topics"] == ["topic1", "topic2"]
        assert data["path"] == "/full/path/to/test.md"
        assert "created" in data

    def test_duplicate_ai_context_file_raises_error(self, registry):
        """Registering duplicate AI context file should raise error."""
        registry.ai_context.register(
            file="test.md",
            project="project1",
            description="First",
            topics=["topic1"]
        )

        with pytest.raises(ValueError, match="already registered"):
            registry.ai_context.register(
                file="test.md",
                project="project2",
                description="Second",
                topics=["topic2"]
            )

    def test_unregister_ai_context(self, registry):
        """Should remove AI context file from registry."""
        registry.ai_context.register(
            file="test.md",
            project="test-project",
            description="Test",
            topics=["test"]
        )

        registry.ai_context.unregister("test.md")

        assert registry.ai_context.get("test.md") is None
        assert len(registry.ai_context.list()) == 0

    def test_list_all_ai_context_files(self, registry):
        """Should list all registered AI context files."""
        registry.ai_context.register(
            file="file1.md",
            project="project1",
            description="First file",
            topics=["topic1"]
        )
        registry.ai_context.register(
            file="file2.md",
            project="project2",
            description="Second file",
            topics=["topic2"]
        )

        contexts = registry.ai_context.list()

        assert len(contexts) == 2
        filenames = [c["file"] for c in contexts]
        assert "file1.md" in filenames
        assert "file2.md" in filenames
