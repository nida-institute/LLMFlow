# StoryFlow Leader's Guide for {{ passage }}

---

## Introduction

{{ intro }}

---

{% for scene_data in scene_steps %}
## Scene {{ loop.index }}: {{ scenes[loop.index0]["Title"] }}

*{{ scenes[loop.index0]["Citation"] }}*

### Step 1: Senses (What's Happening?)
> Step into the scene with your senses.
> What do you see, hear, touch, taste, and feel?
> Picture yourself there as the scene unfolds.
> Look at the scene from the perspective of different characters.
> What do they notice? How do they experience this moment?

{{ scene_data.step1 }}

---

### Step 2: Context (What's the Background?)
> Step into the world of the scene.
> Explore the culture, customs, and daily life of the people in this moment.
> Consider what has happened earlier in the story.
> How does this shape what is happening now?
> How does it help you picture the scene?

{{ scene_data.step2 }}

---

### Step 3: Spiritual and Emotional Journey (What's at the Heart for Them?)
> Step into the thoughts, emotions, and spiritual journey of the characters.
> What were they feeling?
> What struggles or growth were they experiencing?

{{ scene_data.step3 }}

---

### Step 4: Connections (What's at the Heart for Us?)
> What truths or challenges in this scene speak to our lives and faith?
> How does this passage connect with our experiences today?

{{ scene_data.step4 }}

---

{% endfor %}

## Summary (What Do We Call It?)
> What short title captures the heart of this moment?
> What words define this part of the story?

{{ summary }}

- name: assemble_scene_steps
  type: function
  function: llmflow.utils.data.interleave
  inputs:
    json_structure: "${scene_steps_json}"
  outputs: [scene_steps]
