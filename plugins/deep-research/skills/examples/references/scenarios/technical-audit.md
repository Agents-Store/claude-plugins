# Scenario: Technical Audit

**Query:** "Архитектура RAG pipeline — best practices и сравнение подходов"
**Type:** Technical Audit
**Depth:** deep
**Template:** Deep Research Report

## Step-by-Step Execution

### Step 1: CLASSIFY
```
Signals: "архитектура", "best practices", "сравнение подходов" → Technical Audit
Depth: deep (architecture analysis)
```

### Step 2: PLAN
```
expand_query({ query: "RAG pipeline architecture" })

Queries:
1. "RAG pipeline architecture components design"
2. "retrieval augmented generation best practices 2026"
3. "RAG vs fine-tuning comparison"
4. "RAG chunking strategies embedding models"
5. "RAG performance benchmarks evaluation"
6. "production RAG system architecture patterns"
7. "advanced RAG techniques agentic RAG"
```

### Step 3: SEARCH
```
get_code_context_exa({ query: "RAG pipeline implementation architecture" })
→ Code examples and technical context

search_arxiv({ query: "retrieval augmented generation architecture evaluation" })
→ Academic papers

parallel_search_web({
  queries: [
    "RAG best practices production 2026",
    "RAG chunking strategies comparison",
    "RAG evaluation metrics benchmarks"
  ]
})

search({ query: "current state of RAG architecture best practices 2026" })
```

### Step 4: READ
```
sort_by_relevance("RAG architecture best practices", all_urls)
parallel_read_url(top_8_urls)

extract_pdf(arxiv_paper_url) → full paper text for key papers
```

### Step 5: EXTRACT
```
From each source:
- Architecture patterns (naive RAG, advanced RAG, modular RAG)
- Component comparisons (chunkers, embeddings, retrievers, rerankers)
- Performance metrics
- Code patterns and examples
- Failure modes and solutions
```

### Step 6: SYNTHESIZE
```
deduplicate_strings(facts)
Compare architecture approaches across sources
Map consensus vs emerging patterns
Identify implementation trade-offs
```

### Step 7: REPORT
Output: Deep Research Report with:
- Architecture overview (diagram description)
- Component comparison tables
- Best practices per component
- Performance benchmarks
- Code examples
- Common pitfalls
- Recommendations by use case
- Academic references
- Methodology

### Expected Tools Used
`get_code_context_exa`, `search_arxiv`, `parallel_search_web`, `search`, `sort_by_relevance`, `parallel_read_url`, `extract_pdf`, `deduplicate_strings`
