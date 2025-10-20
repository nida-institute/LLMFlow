def test_psalm_pipeline_verse_content_mismatch():
    test_verses = [
        {
            "citation": "Psalm 23:1-3",
            "content": "The LORD is my shepherd; I shall not want. He makes me lie down in green pastures.",
            "expected_title_contains": "Shepherd Provides"
        },
        {
            "citation": "Psalm 23:4",
            "content": "Even though I walk through the valley of the shadow of death, I will fear no evil.",
            "expected_title_contains": "Courage in the Valley"
        },
        {
            "citation": "Psalm 23:5",
            "content": "You prepare a table before me in the presence of my enemies.",
            "expected_title_contains": "Banquet of Abundance"
        },
        {
            "citation": "Psalm 23:6",
            "content": "Surely goodness and mercy shall follow me all the days of my life.",
            "expected_title_contains": "Dwelling in the House"
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            import shutil
            pipeline_source = os.path.join(old_cwd, "pipelines/storyflow-test.yaml")
            pipeline_dest = "storyflow-test.yaml"
            shutil.copy2(pipeline_source, pipeline_dest)

            with open("test_verses.yaml", "w") as f:
                yaml.dump({"verses": test_verses}, f)

            run_pipeline(pipeline_dest)

            output_files = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith("_leaders_guide.md"):
                        output_files.append(os.path.join(root, file))

            assert len(output_files) > 0, f"No leaders guide output found. Files: {os.listdir('.')}"
        finally:
            os.chdir(old_cwd)