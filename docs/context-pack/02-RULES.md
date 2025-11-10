# LLM Assistant Rules for This Project

These are the project-level expectations for any language model interacting with this repository.

1. **Use the context-pack first.**  
   Do not guess architecture or flow syntax when it’s documented here.

2. **LLMFlow YAML is authoritative.**  
   Follow definitions in `llmflow-language.md` and `GPT_CONTEXT.md`.

3. **Never invent pipeline keys.**  
   Only use documented fields: `type`, `inputs`, `outputs`, `vars`, `when`, etc.

4. **Prefer specificity to verbosity.**  
   Reference modules and steps by their actual names.

5. **Be faithful to the design ethos.**  
   Treat flows as narratives of reasoning, not just tasks.

6. **Keep answers embodied and clear.**  
   Explain with short examples from `tutorial.md` when possible.

7. **Distinguish between YAML description and runtime logic.**

8. **When in doubt, ask for the source file by name.**  
   e.g., “Should I consult `architecture.md` or `llmflow-language.md` for this?”

9. **Outputs must serve both humans and machines.**  
   Every generated file or snippet should be readable and executable.

10. **Tone:** technical clarity + interpretive imagination.  
    Think like an engineer who also understands meaning.

---

**Pinned Context Recommendation**

These files should be permanently pinned in Claude or OpenAI chat sessions:

