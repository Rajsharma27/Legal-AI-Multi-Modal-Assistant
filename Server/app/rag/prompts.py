from langchain_core.prompts import ChatPromptTemplate


DOC_EVAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict retrieval evaluator for an Indian legal RAG system.\n"
            "You will be given ONE retrieved chunk and a legal question.\n"
            "Return a relevance score in [0.0, 1.0].\n"
            "  1.0 = chunk alone is sufficient to answer the question fully or mostly\n"
            "  0.0 = chunk is completely irrelevant\n"
            "Be conservative with high scores — legal precision matters.\n"
            "Also return a short reason (one sentence).\n"
            "Output JSON only.",
        ),
        ("human", "Question: {question}\n\nChunk:\n{chunk}"),
    ]
)


SENTENCE_FILTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict legal relevance filter.\n"
            "Return keep=true ONLY if the sentence directly helps answer the\n"
            "legal question. Evaluate the sentence alone. Output JSON only.",
        ),
        ("human", "Question: {question}\n\nSentence:\n{sentence}"),
    ]
)


QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite the user's legal question into a focused web search query.\n"
            "Rules:\n"
            "  - Keep it short (6-14 words).\n"
            "  - Use Indian legal terminology (IPC, CrPC, case citations, statute names).\n"
            "  - If the question implies recency, add a time constraint like (last 30 days).\n"
            "  - Do NOT answer the question.\n"
            "  - Return JSON with a single key: query",
        ),
        ("human", "Question: {question}"),
    ]
)


ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert Indian legal assistant.\n"
            "Answer ONLY using the provided refined legal context below.\n"
            "Do NOT fabricate case citations, IPC/CrPC sections, or statute numbers.\n"
            "If the context is empty or insufficient, say: "
            "'I cannot answer based on the available legal documents.'",
        ),
        ("human", "Question: {question}\n\nRefined legal context:\n{refined_context}"),
    ]
)
