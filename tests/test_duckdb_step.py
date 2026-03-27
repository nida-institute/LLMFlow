"""Tests for DuckDB step type in LLMFlow pipelines"""

import pytest

from llmflow.runner import run_step


class TestDuckDBStepBasics:
    """Test basic DuckDB step execution"""

    def test_simple_query_execution(self, tmp_path):
        """Test executing a simple DuckDB query from a file"""
        # Create query file
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "simple.sql"
        query_file.write_text("SELECT 1 as num, 'hello' as text")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "simple_query",
            "type": "duckdb",
            "query_file": "simple.sql",
            "outputs": "result"
        }

        run_step(step, context, {})

        assert "result" in context
        assert isinstance(context["result"], list)
        assert len(context["result"]) == 1
        assert context["result"][0]["num"] == 1
        assert context["result"][0]["text"] == "hello"

    def test_query_with_variable_substitution(self, tmp_path):
        """Test variable substitution in SQL queries"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "filtered.sql"
        query_file.write_text(
            "SELECT * FROM (VALUES (1, 'a'), (2, 'b'), (3, 'c')) "
            "AS t(num, letter) WHERE num >= ${min_value}"
        )

        context = {
            "queries_dir": str(queries_dir),
            "min_value": 2
        }
        step = {
            "name": "filtered_query",
            "type": "duckdb",
            "query_file": "filtered.sql",
            "inputs": {
                "min_value": "${min_value}"
            },
            "outputs": "filtered_result"
        }

        run_step(step, context, {})

        assert "filtered_result" in context
        assert len(context["filtered_result"]) == 2
        assert context["filtered_result"][0]["num"] == 2
        assert context["filtered_result"][1]["num"] == 3

    def test_query_with_string_variable(self, tmp_path):
        """Test string variable substitution"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "string_filter.sql"
        query_file.write_text(
            "SELECT * FROM (VALUES ('apple', 10), ('banana', 20), ('cherry', 15)) "
            "AS t(fruit, count) WHERE fruit = '${target_fruit}'"
        )

        context = {
            "queries_dir": str(queries_dir),
            "target_fruit": "banana"
        }
        step = {
            "name": "string_query",
            "type": "duckdb",
            "query_file": "string_filter.sql",
            "inputs": {
                "target_fruit": "${target_fruit}"
            },
            "outputs": "fruit_result"
        }

        run_step(step, context, {})

        assert len(context["fruit_result"]) == 1
        assert context["fruit_result"][0]["fruit"] == "banana"
        assert context["fruit_result"][0]["count"] == 20


class TestDuckDBOutputFormats:
    """Test different output format options"""

    def test_records_format_default(self, tmp_path):
        """Test records format (list of dicts) - default"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "test.sql"
        query_file.write_text("SELECT 1 as id, 'test' as name UNION SELECT 2, 'test2'")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "test_query",
            "type": "duckdb",
            "query_file": "test.sql",
            "outputs": "result"
        }

        run_step(step, context, {})

        result = context["result"]
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_dict_format(self, tmp_path):
        """Test dict format (columns as keys)"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "test.sql"
        query_file.write_text("SELECT 1 as id, 'a' as letter UNION SELECT 2, 'b' ORDER BY id")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "test_query",
            "type": "duckdb",
            "query_file": "test.sql",
            "format": "dict",
            "outputs": "result"
        }

        run_step(step, context, {})

        result = context["result"]
        assert isinstance(result, dict)
        assert "id" in result
        assert "letter" in result
        assert result["id"] == [1, 2]
        assert result["letter"] == ["a", "b"]

    def test_json_format(self, tmp_path):
        """Test JSON string format"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "test.sql"
        query_file.write_text("SELECT 1 as id, 'test' as name")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "test_query",
            "type": "duckdb",
            "query_file": "test.sql",
            "format": "json",
            "outputs": "result"
        }

        run_step(step, context, {})

        import json
        result = context["result"]
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["id"] == 1


class TestDuckDBFileReading:
    """Test reading CSV/TSV files with DuckDB"""

    def test_read_csv_auto(self, tmp_path):
        """Test reading CSV files directly"""
        # Create test CSV
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        csv_file = data_dir / "test.csv"
        csv_file.write_text("id,name,value\n1,apple,10\n2,banana,20\n")

        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "read_csv.sql"
        query_file.write_text(
            "SELECT * FROM read_csv_auto('${csv_path}') WHERE value > 10"
        )

        context = {
            "queries_dir": str(queries_dir),
            "csv_path": str(csv_file)
        }
        step = {
            "name": "read_data",
            "type": "duckdb",
            "query_file": "read_csv.sql",
            "inputs": {
                "csv_path": "${csv_path}"
            },
            "outputs": "data"
        }

        run_step(step, context, {})

        assert len(context["data"]) == 1
        assert context["data"][0]["name"] == "banana"

    def test_read_tsv_file(self, tmp_path):
        """Test reading TSV files"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        tsv_file = data_dir / "test.tsv"
        tsv_file.write_text("book\tchapter\tverse\ttext\n"
                           "Genesis\t1\t1\tIn the beginning\n"
                           "Genesis\t1\t2\tAnd the earth\n")

        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "read_tsv.sql"
        query_file.write_text(
            "SELECT book, chapter, COUNT(*) as verse_count "
            "FROM read_csv_auto('${tsv_path}', delim='\\t') "
            "GROUP BY book, chapter"
        )

        context = {
            "queries_dir": str(queries_dir),
            "tsv_path": str(tsv_file)
        }
        step = {
            "name": "count_verses",
            "type": "duckdb",
            "query_file": "read_tsv.sql",
            "inputs": {
                "tsv_path": "${tsv_path}"
            },
            "outputs": "verse_counts"
        }

        run_step(step, context, {})

        assert len(context["verse_counts"]) == 1
        assert context["verse_counts"][0]["verse_count"] == 2


class TestDuckDBErrorHandling:
    """Test error handling for DuckDB steps"""

    def test_missing_query_file(self, tmp_path):
        """Test error when query file doesn't exist"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "missing_file",
            "type": "duckdb",
            "query_file": "nonexistent.sql",
            "outputs": "result"
        }

        with pytest.raises(FileNotFoundError) as exc_info:
            run_step(step, context, {})

        assert "nonexistent.sql" in str(exc_info.value)

    def test_sql_syntax_error(self, tmp_path):
        """Test error handling for invalid SQL"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "bad.sql"
        query_file.write_text("SELECT * FROM nonexistent_table WHERE bad syntax")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "bad_query",
            "type": "duckdb",
            "query_file": "bad.sql",
            "outputs": "result"
        }

        with pytest.raises(Exception):  # DuckDB will raise an error
            run_step(step, context, {})

    def test_missing_variable_error(self, tmp_path):
        """Test error when variable is not in context"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "with_var.sql"
        query_file.write_text("SELECT '${missing_var}' as value")

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "missing_var",
            "type": "duckdb",
            "query_file": "with_var.sql",
            "inputs": {
                "missing_var": "${undefined_variable}"
            },
            "outputs": "result"
        }

        # Variable resolution should leave ${undefined_variable} as-is
        # which will then be in the SQL literally
        run_step(step, context, {})
        # DuckDB will treat it as a literal string
        assert context["result"][0]["value"] == "${undefined_variable}"


class TestDuckDBIntegrationInPipeline:
    """Test DuckDB steps integrated with other step types"""

    def test_duckdb_to_llm_data_flow(self, tmp_path):
        """Test passing DuckDB query results to LLM step"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "frequency.sql"
        query_file.write_text(
            "SELECT 'walk' as lemma, 'הלך' as hebrew, 1543 as frequency "
            "UNION SELECT 'say', 'אמר', 1421"
        )

        context = {"queries_dir": str(queries_dir)}

        # Step 1: DuckDB query
        duckdb_step = {
            "name": "get_verbs",
            "type": "duckdb",
            "query_file": "frequency.sql",
            "outputs": "verb_data"
        }

        run_step(duckdb_step, context, {})

        # Verify data is in context
        assert "verb_data" in context
        assert len(context["verb_data"]) == 2
        assert context["verb_data"][0]["frequency"] == 1543

        # Step 2: Would pass to LLM (we just check context has the data)
        # In real pipeline, LLM would use ${verb_data} in prompt
        assert context["verb_data"] is not None

    def test_chained_duckdb_queries(self, tmp_path):
        """Test chaining multiple DuckDB queries"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()

        # Query 1: Get base data
        query1 = queries_dir / "base.sql"
        query1.write_text(
            "SELECT 'Genesis' as book, 50 as chapters UNION "
            "SELECT 'Exodus', 40 UNION "
            "SELECT 'Leviticus', 27"
        )

        # Query 2: Filter using previous results (simulated via variable)
        query2 = queries_dir / "filtered.sql"
        query2.write_text(
            "SELECT * FROM (VALUES ('Genesis', 50), ('Exodus', 40), ('Leviticus', 27)) "
            "AS t(book, chapters) WHERE chapters >= ${min_chapters}"
        )

        context = {"queries_dir": str(queries_dir)}

        # Execute first query
        step1 = {
            "name": "get_books",
            "type": "duckdb",
            "query_file": "base.sql",
            "outputs": "books"
        }
        run_step(step1, context, {})

        # Set threshold and execute second query
        context["min_chapters"] = 35
        step2 = {
            "name": "filter_books",
            "type": "duckdb",
            "query_file": "filtered.sql",
            "inputs": {
                "min_chapters": "${min_chapters}"
            },
            "outputs": "big_books"
        }
        run_step(step2, context, {})

        assert len(context["big_books"]) == 2  # Genesis and Exodus


class TestDuckDBAdvancedFeatures:
    """Test advanced DuckDB features"""

    def test_window_functions(self, tmp_path):
        """Test window functions for running totals"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "running_total.sql"
        query_file.write_text("""
            SELECT
                chapter,
                words,
                SUM(words) OVER (ORDER BY chapter) as cumulative_words
            FROM (VALUES
                (1, 100),
                (2, 150),
                (3, 200)
            ) AS t(chapter, words)
        """)

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "cumulative",
            "type": "duckdb",
            "query_file": "running_total.sql",
            "outputs": "totals"
        }

        run_step(step, context, {})

        assert len(context["totals"]) == 3
        assert context["totals"][0]["cumulative_words"] == 100
        assert context["totals"][1]["cumulative_words"] == 250
        assert context["totals"][2]["cumulative_words"] == 450

    def test_aggregation_with_grouping(self, tmp_path):
        """Test GROUP BY aggregations"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "group_by.sql"
        query_file.write_text("""
            SELECT
                book,
                COUNT(*) as word_count,
                AVG(frequency) as avg_frequency
            FROM (VALUES
                ('Genesis', 'word1', 10),
                ('Genesis', 'word2', 20),
                ('Exodus', 'word3', 15),
                ('Exodus', 'word4', 25)
            ) AS t(book, word, frequency)
            GROUP BY book
            ORDER BY book
        """)

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "aggregate",
            "type": "duckdb",
            "query_file": "group_by.sql",
            "outputs": "aggregates"
        }

        run_step(step, context, {})

        assert len(context["aggregates"]) == 2
        assert context["aggregates"][0]["book"] == "Exodus"
        assert context["aggregates"][0]["word_count"] == 2
        assert context["aggregates"][1]["book"] == "Genesis"

    def test_empty_result_set(self, tmp_path):
        """Test handling of queries that return no rows"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "empty.sql"
        query_file.write_text(
            "SELECT * FROM (VALUES (1, 'a'), (2, 'b')) AS t(id, val) WHERE id > 10"
        )

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "empty_query",
            "type": "duckdb",
            "query_file": "empty.sql",
            "outputs": "empty_result"
        }

        run_step(step, context, {})

        assert "empty_result" in context
        assert isinstance(context["empty_result"], list)
        assert len(context["empty_result"]) == 0


class TestDuckDBStepConfiguration:
    """Test various configuration options for DuckDB steps"""

    def test_absolute_query_file_path(self, tmp_path):
        """Test using absolute path for query file"""
        query_file = tmp_path / "absolute_query.sql"
        query_file.write_text("SELECT 42 as answer")

        context = {}
        step = {
            "name": "absolute_path",
            "type": "duckdb",
            "query_file": str(query_file),
            "outputs": "result"
        }

        run_step(step, context, {})

        assert context["result"][0]["answer"] == 42

    def test_step_with_saveas(self, tmp_path):
        """Test DuckDB step with saveas directive"""
        queries_dir = tmp_path / "queries"
        queries_dir.mkdir()
        query_file = queries_dir / "test.sql"
        query_file.write_text("SELECT 'test' as value")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_file = output_dir / "result.json"

        context = {"queries_dir": str(queries_dir)}
        step = {
            "name": "save_query",
            "type": "duckdb",
            "query_file": "test.sql",
            "outputs": "result",
            "saveas": str(output_file),
            "format": "json"
        }

        run_step(step, context, {})

        assert output_file.exists()
        import json
        saved_data = json.loads(output_file.read_text())
        assert saved_data[0]["value"] == "test"
