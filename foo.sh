if cat obsidian/grc/intermediate/ο./ὁ.refs.json | python3 -c "import sys, json; d=json.load(sys.stdin); print('Has lemma key:', 'lemma' in d); print('Has references key:', 'references' in d); print('Type of root:', type(d).__name__)"; then
    echo "Successfully parsed JSON"
else
    echo "Failed to parse JSON"
fi

echo -e "\n=== Last 50 lines of log for analyze-references ==="
tail -200 llmflow.log | grep -B 5 -A 10 "analyze-references"
