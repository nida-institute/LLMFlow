import pytest
import tempfile
import yaml
import os
import re
from llmflow.runner import run_pipeline

def test_psalm_pipeline_verse_content_mismatch():
    """Test the actual psalm pipeline for verse content misalignment bug"""
    
    # Create minimal test data that simulates your pipeline issue
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
            # Copy the actual pipeline
            import shutil
            pipeline_source = os.path.join(old_cwd, "pipelines/storyflow-psalms-editing.yaml")
            pipeline_dest = "storyflow-psalms-editing.yaml"
            shutil.copy2(pipeline_source, pipeline_dest)
            
            # Create mock data file
            with open("test_verses.yaml", "w") as f:
                yaml.dump({"verses": test_verses}, f)
            
            # Run the actual pipeline
            # You might need to modify this based on how your pipeline accepts input
            run_pipeline(pipeline_dest)
            
            # Check if output was generated
            output_files = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith("_leaders_guide.md"):
                        output_files.append(os.path.join(root, file))
            
            assert len(output_files) > 0, f"No leaders guide output found. Files: {os.listdir('.')}"
            
            # Read the output
            with open(output_files[0], 'r') as f:
                content = f.read()
            
            print("=== GENERATED CONTENT ===")
            print(content[:2000])  # First 2000 chars for debugging
            
            # Extract scenes
            scenes = re.findall(r'# Scene: (.+?)\n\n\*Citation: (.+?)\*\n\n(.+?)(?=# Scene:|---\n\n## Summary|$)', content, re.DOTALL)
            
            print(f"\n=== FOUND {len(scenes)} SCENES ===")
            for i, (title, citation, scene_content) in enumerate(scenes):
                print(f"Scene {i+1}: {title} -> {citation}")
                print(f"Content preview: {scene_content[:100]}...")
                print()
            
            # Critical assertion: verify title/content alignment
            for i, (title, citation, scene_content) in enumerate(scenes):
                expected_verse = test_verses[i]
                
                # Check title alignment
                assert expected_verse["expected_title_contains"] in title, \
                    f"Scene {i+1}: Expected title to contain '{expected_verse['expected_title_contains']}', got '{title}'"
                
                # Check citation alignment  
                assert expected_verse["citation"] == citation, \
                    f"Scene {i+1}: Expected citation '{expected_verse['citation']}', got '{citation}'"
                
                # This is the key test: content should match the citation
                # Look for verse numbers in the content to detect misalignment
                verse_numbers_in_content = re.findall(r'Psalm 23:(\d+(?:-\d+)?)', scene_content)
                expected_verse_num = expected_verse["citation"].split(":")[-1]
                
                if verse_numbers_in_content:
                    content_verse_num = verse_numbers_in_content[0]
                    assert content_verse_num == expected_verse_num, \
                        f"Scene {i+1}: Content contains verse {content_verse_num} but citation is {expected_verse_num}. CONTENT MISMATCH DETECTED!"
        
        finally:
            os.chdir(old_cwd)

def test_for_each_variable_binding_isolation():
    """Test that for-each properly isolates variables between iterations"""
    
    pipeline = {
        "name": "test-variable-binding",
        "steps": [
            {
                "name": "create_test_data",
                "type": "function", 
                "function": "tests.test_regression_scene_duplication.create_test_verses",
                "outputs": "verses"
            },
            {
                "name": "process_verses",
                "type": "for-each",
                "input": "${verses}",
                "item_var": "verse",
                "steps": [
                    {
                        "name": "mock_llm_call",
                        "type": "function",
                        "function": "tests.test_regression_scene_duplication.mock_llm_response", 
                        "inputs": {
                            "verse": "${verse}",
                            "citation": "${verse.citation}"
                        },
                        "outputs": "scene_data",
                        "append_to": "all_scenes"
                    }
                ]
            },
            {
                "name": "save_debug",
                "type": "save",
                "input": "${all_scenes}",
                "filename": "debug_scenes.json",
                "format": "json"
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, 'w') as f:
            yaml.dump(pipeline, f)
        
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            run_pipeline(pipeline_file)
            
            with open("debug_scenes.json") as f:
                import json
                scenes = json.load(f)
            
            print("=== VARIABLE BINDING TEST ===")
            for i, scene in enumerate(scenes):
                print(f"Scene {i+1}: Citation='{scene['citation']}' -> Content='{scene['content'][:50]}...'")
            
            # Check that each scene has the correct content for its citation
            for i, scene in enumerate(scenes):
                citation = scene['citation']
                content = scene['content']
                
                # Extract verse number from citation
                verse_match = re.search(r':(\d+)', citation)
                if verse_match:
                    verse_num = verse_match.group(1)
                    # Content should mention the same verse number
                    assert f"verse_{verse_num}" in content, \
                        f"Scene {i+1}: Citation {citation} but content doesn't match: {content}"
                        
        finally:
            os.chdir(old_cwd)

def create_test_verses():
    """Create test verses that help detect variable binding issues"""
    return [
        {"citation": "Psalm 23:1", "verse_text": "The LORD is my shepherd"},
        {"citation": "Psalm 23:2", "verse_text": "He makes me lie down"}, 
        {"citation": "Psalm 23:3", "verse_text": "He restores my soul"},
        {"citation": "Psalm 23:4", "verse_text": "Even though I walk through the valley"}
    ]

def mock_llm_response(verse, citation):
    """Mock LLM that returns content tied to the specific verse"""
    # Extract verse number to ensure content matches citation
    verse_match = re.search(r':(\d+)', citation)
    verse_num = verse_match.group(1) if verse_match else "unknown"
    
    return {
        "citation": citation,
        "content": f"This is content for verse_{verse_num}: {verse.get('verse_text', 'default text')}",
        "title": f"Scene for verse {verse_num}"
    }