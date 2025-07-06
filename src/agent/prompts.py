from langchain_core.prompts import ChatPromptTemplate

# Extract slots prompt
EXTRACT_SLOTS_PROMPT = ChatPromptTemplate.from_template("""
You are analyzing a research question to identify what information slots need to be filled to provide a complete answer.

Question: {question}

Identify the key information slots that need to be gathered. For example:
- For "What are the best restaurants in Paris?" → slots: ["location", "cuisine_type", "price_range", "rating"]
- For "Compare Python vs JavaScript" → slots: ["language1", "language2", "comparison_aspects"]
- For "History of World War II" → slots: ["time_period", "geographic_scope", "key_events", "major_participants"]

Return ONLY a JSON array of slot names, no other text:
["slot1", "slot2", "slot3"]
""")

# GenerateQueries prompt
GENERATE_QUERIES_PROMPT = ChatPromptTemplate.from_template("""
You are a research assistant. Break down the following question into 3-5 specific search queries that will help find relevant information.

Question: {question}

Generate search queries that are:
- Specific and focused
- Use different keywords and approaches
- Cover different aspects of the question
- Likely to return relevant results

Return ONLY a JSON array of strings, no other text (no markdown formatting, no code blocks):
["query1", "query2", "query3", "query4", "query5"]
""")

# Reflect prompt
REFLECT_PROMPT = ChatPromptTemplate.from_template("""
You are evaluating whether the current search results are sufficient to answer the question using a comprehensive slot-based approach.

Question: {question}

Current search results:
{docs}

STEP 1: Identify MANDATORY information slots
Analyze the question and identify ALL mandatory information slots that must be filled to provide a complete answer. Consider:

WHO questions: winner, loser, participants, key_people, team, organization
WHAT questions: definition, description, features, characteristics, components
WHEN questions: date, time_period, duration, timeline, year
WHERE questions: location, place, venue, country, region
HOW questions: method, process, steps, mechanism, approach
WHY questions: cause, reason, purpose, motivation, explanation

For complex questions, identify multiple slots:
- "Who won the 2022 World Cup?" → slots: ["winner", "opponent", "score", "date", "venue"]
- "What is machine learning?" → slots: ["definition", "types", "applications", "advantages"]
- "When did World War II end?" → slots: ["end_date", "end_location", "key_events", "participants"]

STEP 2: Match evidence sentences to slots
For each identified slot, carefully examine the search results and:
- Look for specific sentences that provide information for each slot
- Check for consistency across multiple sources
- Identify if information is missing, partial, or conflicting
- Only mark a slot as "filled" if you have clear, consistent evidence

STEP 3: Judge completeness and consistency
- If ALL mandatory slots have clear, consistent evidence → need_more = false
- If ANY mandatory slots are missing, unclear, or have conflicting information → need_more = true
- Generate targeted queries specifically for missing or unclear slots

Return ONLY a JSON object with this exact format (no markdown formatting, no code blocks):
{{
    "slots": ["slot1", "slot2", "slot3"],
    "filled": ["slot1", "slot2"],
    "need_more": true/false,
    "new_queries": ["targeted query for missing slot", "another targeted query"]
}}

CRITICAL RULES:
1. Only mark slots as "filled" if you have clear, consistent evidence from the search results
2. If there's conflicting information for a slot, mark it as unfilled and need_more = true
3. If information is partial or unclear, mark it as unfilled and need_more = true
4. Generate specific queries targeting the exact missing information
5. need_more = false ONLY when ALL slots are filled with consistent evidence

Examples:
- "Who won the 2022 World Cup?" 
  → slots: ["winner", "opponent", "score", "date"]
  → if only winner found: filled: ["winner"], need_more: true, new_queries: ["France Argentina 2022 World Cup final score", "2022 World Cup final date"]

- "What is Python?"
  → slots: ["definition", "features", "use_cases"]
  → if definition and features found: filled: ["definition", "features"], need_more: true, new_queries: ["Python programming use cases applications"]

- Complete information example:
  → slots: ["winner", "score", "date"], filled: ["winner", "score", "date"], need_more: false, new_queries: []
""")

# Synthesize prompt
SYNTHESIZE_PROMPT = ChatPromptTemplate.from_template("""
You are a research assistant. Based on the search results, provide a direct and concise answer to the question.

Question: {question}
Required slots: {slots}
Filled slots: {filled_slots}

Search results:
{docs}

Requirements:
- Answer must be DIRECT and CONCISE (maximum 80 words, approximately 400 characters)
- Start with the most important fact that directly answers the question
- Do NOT use phrases like "Based on the search results" or "Here's what I found"
- Be factual and accurate - only include information that directly answers the question
- End with Markdown-style citations [1][2][3]... referencing the sources used
- Focus on the core answer, not peripheral details

Examples of good answers:
- "Argentina won the 2022 FIFA World Cup, beating France on penalties after a 3-3 draw in extra time.[1]"
- "Python is a high-level, interpreted programming language known for its simplicity and readability.[1]"
- "The Great Wall of China is approximately 13,171 miles (21,196 kilometers) long.[1]"

Return ONLY a JSON object with this exact format (no markdown formatting, no code blocks):
{{
    "answer": "Your direct and concise answer here with [1][2] citations at the end",
    "citations": [
        {{
            "id": 1,
            "title": "Source Title",
            "url": "https://example.com/source"
        }},
        {{
            "id": 2,
            "title": "Another Source",
            "url": "https://example.com/another"
        }}
    ]
}}

The citations array should contain structured objects with id (matching the citation numbers in your answer), title, and url for each source you referenced.
""") 