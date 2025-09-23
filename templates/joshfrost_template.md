# Josh Frost Emotional Exegesis: {{ passage }}

{% for scene in scenes %}
## {{ scene["Scene number"] }}: {{ scene["Title"] }}

*{{ scene["Citation"] }}*

{{ joshfrost_content[loop.index0] }}

---

{% endfor %}