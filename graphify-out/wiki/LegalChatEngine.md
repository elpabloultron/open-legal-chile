# LegalChatEngine

> 45 nodes · cohesion 0.07

## Key Concepts

- **LegalChatEngine** (28 connections) — `chat_engine.py`
- **.chat()** (13 connections) — `chat_engine.py`
- **test_chat_and_critique.py** (13 connections) — `tests/test_chat_and_critique.py`
- **LegalCritiqueEngine** (12 connections) — `critique.py`
- **.detect_provider()** (10 connections) — `chat_engine.py`
- **check_configuration()** (6 connections) — `config.py`
- **.call_anthropic()** (5 connections) — `chat_engine.py`
- **.call_deepseek()** (5 connections) — `chat_engine.py`
- **.call_gemini()** (5 connections) — `chat_engine.py`
- **.critique()** (5 connections) — `critique.py`
- **run_benchmark()** (5 connections) — `evals/benchmark.py`
- **get_relevant_legal_context()** (4 connections) — `chat_engine.py`
- **.call_ollama()** (4 connections) — `chat_engine.py`
- **.call_openai()** (4 connections) — `chat_engine.py`
- **.resolve_model()** (4 connections) — `chat_engine.py`
- **.verify_credentials()** (4 connections) — `chat_engine.py`
- **.call_soberano_local()** (3 connections) — `chat_engine.py`
- **.is_ollama_available()** (3 connections) — `chat_engine.py`
- **LD-07 — Transparencia sobre la IA y los datos** (3 connections) — `docs/legal_design.md`
- **evaluate_response()** (3 connections) — `evals/benchmark.py`
- **test_detect_provider_defaults_to_soberano_or_ollama()** (3 connections) — `tests/test_chat_and_critique.py`
- **Any** (2 connections)
- **.__init__()** (2 connections) — `critique.py`
- **Any** (2 connections)
- **test_check_configuration_sovereign()** (2 connections) — `tests/test_chat_and_critique.py`
- *... and 20 more nodes in this community*

## Relationships

- [os](os.md) (20 shared connections)
- [mcp_server.py](mcp_server.py.md) (7 shared connections)
- [BaseLegalAgent](BaseLegalAgent.md) (6 shared connections)
- [2. Las 12 reglas](2._Las_12_reglas.md) (1 shared connections)

## Source Files

- `chat_engine.py`
- `config.py`
- `critique.py`
- `docs/legal_design.md`
- `evals/benchmark.py`
- `tests/test_chat_and_critique.py`

## Audit Trail

- EXTRACTED: 98 (94%)
- INFERRED: 6 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*