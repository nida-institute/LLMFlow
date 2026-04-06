from llmflow.runner import resolve, get_from_context


class TestResolveFunction:
    """Test the resolve function with various variable patterns"""

    def test_simple_variable(self):
        """Test basic variable resolution"""
        context = {"name": "John", "age": 30}
        assert resolve("${name}", context) == "John"
        assert resolve("${age}", context) == 30

    def test_list_indexing(self):
        """Test list indexing with positive and negative indices"""
        context = {
            "items": ["first", "second", "third", "fourth"],
            "numbers": [10, 20, 30, 40],
        }

        # Positive indices
        assert resolve("${items[0]}", context) == "first"
        assert resolve("${items[2]}", context) == "third"
        assert resolve("${numbers[1]}", context) == 20

        # Negative indices
        assert resolve("${items[-1]}", context) == "fourth"
        assert resolve("${items[-2]}", context) == "third"
        assert resolve("${numbers[-1]}", context) == 40

    def test_nested_resolution(self):
        """Test nested object resolution"""
        context = {"user": {"name": "Alice", "scores": [85, 90, 95]}}

        assert resolve("${user.name}", context) == "Alice"
        assert resolve("${user.scores[0]}", context) == 85
        assert resolve("${user.scores[-1]}", context) == 95

    def test_template_variables(self):
        """Test the exact pattern used in templates"""
        context = {
            "bodies_list": ["body1", "body2", "body3"],
            "hearts_list": ["heart1", "heart2", "heart3"],
            "scene": {"title": "Scene 1", "number": 1},
        }

        # These are the exact patterns failing in your templates
        assert resolve("${bodies_list[-1]}", context) == "body3"
        assert resolve("${hearts_list[-1]}", context) == "heart3"
        assert resolve("${scene.title}", context) == "Scene 1"

    # NEW TESTS FOR BRACKET NOTATION

    def test_dict_bracket_notation_unquoted(self):
        """Test ${row[lemma]} - unquoted bracket notation with dict"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the", "strongs": "G3588"}
        }

        # Unquoted bracket notation should work
        assert resolve("${row[lemma]}", context) == "ὁ"
        assert resolve("${row[gloss]}", context) == "the"
        assert resolve("${row[strongs]}", context) == "G3588"

    def test_dict_bracket_notation_single_quotes(self):
        """Test ${row['lemma']} - single-quoted bracket notation"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the"}
        }

        assert resolve("${row['lemma']}", context) == "ὁ"
        assert resolve("${row['gloss']}", context) == "the"

    def test_dict_bracket_notation_double_quotes(self):
        """Test ${row["lemma"]} - double-quoted bracket notation"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the"}
        }

        assert resolve('${row["lemma"]}', context) == "ὁ"
        assert resolve('${row["gloss"]}', context) == "the"

    def test_row_object_with_getitem(self):
        """Test Row objects that support __getitem__ (like TSV plugin)"""
        class Row:
            def __init__(self, data):
                self.data = data

            def __getitem__(self, key):
                return self.data[key]

            def __getattr__(self, key):
                return self.data.get(key)

        context = {
            "row": Row({"lemma": "ὁ", "gloss": "the", "status": "pending"})
        }

        # Both notations should work with Row objects
        assert resolve("${row[lemma]}", context) == "ὁ"
        assert resolve("${row['lemma']}", context) == "ὁ"
        assert resolve("${row.lemma}", context) == "ὁ"

    def test_bracket_notation_in_xpath_expression(self):
        """Test bracket notation in XPath expressions (real use case)"""
        context = {
            "row": {"lemma": "ὁ", "strongs": "G3588"}
        }

        # XPath with unquoted bracket notation
        result = resolve("//tei:entry[@key='${row[lemma]}']", context)
        assert result == "//tei:entry[@key='ὁ']"

        # XPath with quoted bracket notation
        result = resolve("//tei:entry[@strongs='${row['strongs']}']", context)
        assert result == "//tei:entry[@strongs='G3588']"

    def test_bracket_notation_in_file_paths(self):
        """Test bracket notation in saveas file paths (real use case)"""
        context = {
            "row": {"lemma": "ὁ", "strongs": "G3588"}
        }

        # Unquoted bracket notation in path
        result = resolve("outputs/xml/${row[lemma]}.xml", context)
        assert result == "outputs/xml/ὁ.xml"

        # Quoted bracket notation in path
        result = resolve("outputs/json/${row['strongs']}.json", context)
        assert result == "outputs/json/G3588.json"

    def test_bracket_notation_with_special_characters(self):
        """Test bracket notation with keys containing special characters"""
        context = {
            "data": {
                "key-with-dash": "value1",
                "key.with.dots": "value2",
                "key with spaces": "value3"
            }
        }

        # Must use quoted notation for special characters
        assert resolve("${data['key-with-dash']}", context) == "value1"
        assert resolve("${data['key.with.dots']}", context) == "value2"
        assert resolve("${data['key with spaces']}", context) == "value3"

    def test_bracket_notation_with_unicode(self):
        """Test bracket notation with Unicode keys and values"""
        context = {
            "lexicon": {
                "ὁ": "the",
                "θεός": "God",
                "λόγος": "word"
            }
        }

        assert resolve("${lexicon['ὁ']}", context) == "the"
        assert resolve("${lexicon['θεός']}", context) == "God"
        assert resolve("${lexicon['λόγος']}", context) == "word"

    def test_mixed_dot_and_bracket_notation(self):
        """Test mixing dot and bracket notation"""
        context = {
            "data": {
                "items": [
                    {"name": "first", "value": 1},
                    {"name": "second", "value": 2}
                ]
            }
        }

        # Access nested structure with mixed notation
        result = resolve("${data.items[0]}", context)
        assert result == {"name": "first", "value": 1}

        # Access list then dict key
        result = resolve("${data.items[1]}", context)
        assert result == {"name": "second", "value": 2}

    def test_empty_context(self):
        """Test resolution with missing variables"""
        context = {}

        # Should return original string if variable not found
        assert resolve("${missing}", context) == "${missing}"
        assert resolve("${row[lemma]}", context) == "${row[lemma]}"

    def test_none_values_in_context(self):
        """Test resolution when context has None values"""
        context = {
            "data": {"key": None}
        }

        # When a value is None, resolve returns the original template string
        # (because None is falsy in the resolution logic)
        result = resolve("${data.key}", context)
        # Current behavior: returns unresolved template when value is None
        assert result == "${data.key}"

        # For a missing key entirely:
        context2 = {"data": {}}
        result2 = resolve("${data.missing}", context2)
        assert result2 == "${data.missing}"


class TestGetFromContext:
    """Test the get_from_context helper function directly"""

    def test_simple_dict_access(self):
        """Test simple dictionary access"""
        context = {"name": "John", "age": 30}

        assert get_from_context("name", context) == "John"
        assert get_from_context("age", context) == 30

    def test_bracket_notation_unquoted(self):
        """Test bracket notation without quotes"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the"}
        }

        result = get_from_context("row[lemma]", context)
        assert result == "ὁ", f"Expected 'ὁ', got {result}"

        result = get_from_context("row[gloss]", context)
        assert result == "the", f"Expected 'the', got {result}"

    def test_bracket_notation_single_quoted(self):
        """Test bracket notation with single quotes"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the"}
        }

        result = get_from_context("row['lemma']", context)
        assert result == "ὁ", f"Expected 'ὁ', got {result}"

    def test_bracket_notation_double_quoted(self):
        """Test bracket notation with double quotes"""
        context = {
            "row": {"lemma": "ὁ", "gloss": "the"}
        }

        result = get_from_context('row["lemma"]', context)
        assert result == "ὁ", f"Expected 'ὁ', got {result}"

    def test_dot_notation(self):
        """Test dot notation"""
        context = {
            "user": {"name": "John", "profile": {"city": "NYC"}}
        }

        result = get_from_context("user.name", context)
        assert result == "John"

        result = get_from_context("user.profile.city", context)
        assert result == "NYC"

    def test_numeric_indexing(self):
        """Test numeric array indexing"""
        context = {
            "items": ["a", "b", "c"]
        }

        result = get_from_context("items[0]", context)
        assert result == "a"

        result = get_from_context("items[2]", context)
        assert result == "c"

    def test_row_object_bracket_access(self):
        """Test Row objects that support __getitem__"""
        class Row:
            def __init__(self, data):
                self.data = data

            def __getitem__(self, key):
                return self.data[key]

        context = {
            "row": Row({"lemma": "ὁ", "gloss": "the"})
        }

        result = get_from_context("row[lemma]", context)
        assert result == "ὁ"

        result = get_from_context("row['lemma']", context)
        assert result == "ὁ"


class TestSliceNotation:
    """Test Python slice notation in variable references"""

    def test_basic_slice_last_n(self):
        """Test ${list[-3:]} - get last 3 items"""
        context = {
            "my_list": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        }

        result = resolve("${my_list[-3:]}", context)
        assert result == ["h", "i", "j"]

        result = resolve("${my_list[-1:]}", context)
        assert result == ["j"]

        result = resolve("${my_list[-5:]}", context)
        assert result == ["f", "g", "h", "i", "j"]

    def test_basic_slice_first_n(self):
        """Test ${list[:n]} - get first n items"""
        context = {
            "my_list": ["a", "b", "c", "d", "e", "f"]
        }

        result = resolve("${my_list[:2]}", context)
        assert result == ["a", "b"]

        result = resolve("${my_list[:1]}", context)
        assert result == ["a"]

        result = resolve("${my_list[:5]}", context)
        assert result == ["a", "b", "c", "d", "e"]

    def test_slice_middle_range(self):
        """Test ${list[start:stop]} - get items from start to stop"""
        context = {
            "my_list": ["a", "b", "c", "d", "e", "f", "g", "h"]
        }

        result = resolve("${my_list[2:5]}", context)
        assert result == ["c", "d", "e"]

        result = resolve("${my_list[0:3]}", context)
        assert result == ["a", "b", "c"]

        result = resolve("${my_list[3:7]}", context)
        assert result == ["d", "e", "f", "g"]

    def test_slice_negative_indices(self):
        """Test ${list[start:stop]} with negative indices"""
        context = {
            "my_list": ["a", "b", "c", "d", "e", "f"]
        }

        result = resolve("${my_list[-5:-2]}", context)
        assert result == ["b", "c", "d"]

        result = resolve("${my_list[-3:-1]}", context)
        assert result == ["d", "e"]

    def test_slice_with_step(self):
        """Test ${list[start:stop:step]} - with step parameter"""
        context = {
            "my_list": ["a", "b", "c", "d", "e", "f", "g", "h"]
        }

        # Every other item
        result = resolve("${my_list[::2]}", context)
        assert result == ["a", "c", "e", "g"]

        # Every third item starting from index 1
        result = resolve("${my_list[1::3]}", context)
        assert result == ["b", "e", "h"]

        # Range with step
        result = resolve("${my_list[1:7:2]}", context)
        assert result == ["b", "d", "f"]

    def test_slice_edge_cases(self):
        """Test edge cases: empty lists, out of bounds, etc."""
        context = {
            "empty": [],
            "small": ["a", "b"],
            "items": ["x", "y", "z"]
        }

        # Empty list
        result = resolve("${empty[-3:]}", context)
        assert result == []

        # Slice beyond list bounds (Python semantics: no error)
        result = resolve("${small[-10:]}", context)
        assert result == ["a", "b"]

        result = resolve("${items[:100]}", context)
        assert result == ["x", "y", "z"]

        # Entire list
        result = resolve("${items[:]}", context)
        assert result == ["x", "y", "z"]

        # Empty slice
        result = resolve("${items[5:10]}", context)
        assert result == []

    def test_slice_non_list_values(self):
        """Test slice notation on non-list values"""
        context = {
            "string": "hello",
            "number": 42,
            "dict": {"key": "value"}
        }

        # Slice on string should work (Python slices strings)
        result = resolve("${string[-3:]}", context)
        assert result == "llo"

        result = resolve("${string[:2]}", context)
        assert result == "he"

        # Slice on non-sequence types should return None or original
        result = resolve("${number[-3:]}", context)
        assert result == "${number[-3:]}"  # Can't slice int

        result = resolve("${dict[:2]}", context)
        assert result == "${dict[:2]}"  # Can't slice dict

    def test_slice_combined_with_wildcard(self):
        """Test ${list[-3:][*].field} - slice then wildcard extraction"""
        context = {
            "pericope_results": [
                {"id": 1, "analysis": "analysis 1", "title": "Title 1"},
                {"id": 2, "analysis": "analysis 2", "title": "Title 2"},
                {"id": 3, "analysis": "analysis 3", "title": "Title 3"},
                {"id": 4, "analysis": "analysis 4", "title": "Title 4"},
                {"id": 5, "analysis": "analysis 5", "title": "Title 5"},
            ]
        }

        # Get last 3 analyses (the actual use case from issue #116)
        result = resolve("${pericope_results[-3:][*].analysis}", context)
        assert result == ["analysis 3", "analysis 4", "analysis 5"]

        # Get first 2 titles
        result = resolve("${pericope_results[:2][*].title}", context)
        assert result == ["Title 1", "Title 2"]

        # Get middle range IDs
        result = resolve("${pericope_results[1:4][*].id}", context)
        assert result == [2, 3, 4]

    def test_slice_in_string_substitution(self):
        """Test slice notation in string substitution (not exact match)"""
        context = {
            "items": ["apple", "banana", "cherry"]
        }

        # In mid-string substitution
        result = resolve("Last item is ${items[-1:]}", context)
        assert result == "Last item is ['cherry']"

    def test_slice_with_nested_objects(self):
        """Test slicing nested objects then accessing fields"""
        context = {
            "data": {
                "records": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25},
                    {"name": "Charlie", "age": 35},
                    {"name": "Diana", "age": 28},
                ]
            }
        }

        # Slice nested list
        result = resolve("${data.records[-2:]}", context)
        assert result == [
            {"name": "Charlie", "age": 35},
            {"name": "Diana", "age": 28},
        ]

        # Slice then access first item
        result = resolve("${data.records[:2][0]}", context)
        assert result == {"name": "Alice", "age": 30}

    def test_get_from_context_slice(self):
        """Test get_from_context directly with slice notation"""
        context = {
            "items": ["a", "b", "c", "d", "e"]
        }

        result = get_from_context("items[-3:]", context)
        assert result == ["c", "d", "e"]

        result = get_from_context("items[:2]", context)
        assert result == ["a", "b"]

        result = get_from_context("items[1:4]", context)
        assert result == ["b", "c", "d"]
