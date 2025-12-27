# Scene Files

This directory contains scene lists for biblical passages in JSON format.

Each scene file contains an array of scenes with:
- **Scene number**: Sequential identifier
- **Citation**: Biblical reference
- **Title**: Scene title
- **Berean Standard Bible** or **WLC**: Text in English or Hebrew
- **SBLGNT**: Greek text (for NT passages)

These scenes are inputs for the visual commentary pipeline.

## Example files:

- `Psalm_23.json` - Psalm 23 (4 scenes)
- `Psalm_1.json` - Psalm 1 (3 scenes)  
- `Matthew_2_13_23.json` - Matthew 2:13-23 (3 scenes)

## Usage:

\`\`\`bash
llmflow run --pipeline pipelines/visual-commentary.yaml --var passage="Psalm 23"
\`\`\`

The pipeline will look for `scenes/Psalm_23.json` based on the passage reference.
