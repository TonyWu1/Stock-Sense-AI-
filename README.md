# StockSense AI 2.0 — Smart Inventory & Purchasing

**Amazon Build, Ship, Shape Hackathon 2026 · Alexa+ track (simulated experience)**

StockSense AI is a Streamlit business operations web app with a Python/SQLite backend and an OpenAI-powered **Alexa+-inspired text simulation**. It is **not** an Amazon Alexa skill or connected to Alexa hardware/services.

The owner can inspect a sample grocery inventory, compare stockout risk against **simulated** supplier lead times, choose a spending cap, create a saved SQLite purchase-order draft, and explicitly approve it locally. An LLM-powered assistant can invoke the same application functions through tool/function calling; the LLM has **no approval tool**.

## Features

- Dashboard with SQLite-backed counts, stock alerts, and Operations Brief.
- Searchable inventory gallery, add-product form, and exported product list.
- Explainable Smart Restock Decision Lab with $50/$150 budget and supplier-delay scenarios.
- Visual manual purchase-order builder, per-supplier totals, budget gauge, draft-overlap warnings.
- Local SQLite order history with separate, explicit approval confirmation.
- Conversational agent with tools to read real inventory, plan purchases, and save drafts.
- UI suitable for a simulated Alexa+ experience. **No real supplier purchases, payments, or stock receipts.**

## Quickstart (Windows / PowerShell)

Requires **Python 3.12** and an internet connection for the optional live AI Assistant.

```powershell
cd <PATH_TO_THIS_01_GITHUB_PROJECT_FOLDER>
py -3.12 -m venv .venv_hackathon
.\.venv_hackathon\Scripts\python.exe -m pip install -r requirements.txt
.\.venv_hackathon\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Open **http://localhost:8502**. No activation script is needed. On first launch, the local database is created automatically at `data/stocksense.db` with 15 **simulated** sample grocery products. The core Dashboard, Inventory, Decision Lab, and Purchase Orders functions do **not** need an API key.

### Optional real AI conversation

1. Copy `.env.example` to `.env` in the project root.
2. Put your **own** OpenAI API key in `OPENAI_API_KEY` inside `.env`; leave `OPENAI_MODEL=gpt-4.1-mini` or set a compatible accessible model.
3. Restart Streamlit and open AI Assistant.
4. Ask `Which products are running low?` to start with a read-only query.
5. Try `Prepare a smart restock order under $50 with a three-day simulated supplier delay.` Then inspect the **draft** in Purchase Orders. Approval is a **separate local action**.

**Credentials:** Never commit `.env` or paste your key into issue tickets, screenshots, or README files. OpenAI API calls may incur charges. API billing is separate from ChatGPT.

## Try the full workflow without a paid API

- **Dashboard:** Run $50 / 3-day delay in Decision Lab; the result is a read-only preview.
- **Inventory:** Add a sample product or view the seeded catalog.
- **Purchase Orders:** Create a manual cart or generate a smart restock draft, review the amount, then explicitly approve the local record.
- **AI Assistant:** Requires your own API key for the live conversational flow; it is not an offline LLM.

## Tests

Tests use temporary SQLite databases and do not modify the application's actual `data/stocksense.db`:

```powershell
.\.venv_hackathon\Scripts\python.exe -m unittest discover -s tests -v
```

The packaged source passed **45 automated isolated tests** in the preparation environment on 2026-10-23. These tests include mock AI responses; they are not a substitute for a live API browser test.

## Source layout

| File | Role |
|---|---|
| `app.py` | Streamlit app and four-page navigation |
| `visual_workflows.py` | Product cards, cart, purchase-builder presentation |
| `assistant_page.py` | Alexa+-inspired conversational UI |
| `agent.py` | OpenAI Chat Completions tool/function calling and confirmation guard |
| `backend_adapter.py` | Stable service interface |
| `backend.py` | SQLite products and purchase-order persistence |
| `decision_engine.py` | Transparent, budget-aware heuristic restocking calculator |
| `tests/` | Local backend and headless UI tests |
| `.env.example` | Safe placeholder for optional API configuration |
| `docs/` | Judge quickstart, limitations, and security notes |

## Architecture

```text
Streamlit (app.py)
  ├─ Inventory / Dashboard / Purchasing widgets
  │     └─ InventoryBackend → backend.py → SQLite
  └─ Alexa+-inspired chat → agent.py → tool calling → InventoryBackend
                                               └─ decision_engine.py
```

The backend computes prices and enforces budgets **server-side**. The model cannot directly approve or send orders. `approve_order(..., confirmed=True)` is only called following explicit owner action.

## Honest limitations

- All catalog data and sales history are sample/simulated. Actual business inventory was not connected.
- Supplier lead-time and shelf-life values are illustrative assumptions; seven-day averages are heuristics, **not** validated demand forecasts or proven savings.
- Local order approval changes only database status and does not purchase, pay for, receive, or ship inventory.
- Duplicate-draft warnings are local and scoped to accessible order history, not a production-wide idempotency system.
- The application has no real Alexa+, Amazon account, MCP, payment, or supplier system integration.
- Local Streamlit is not a public hosted app; reviewers can reproduce the core functions using the instructions above.

## Video and judge materials

For the uploaded demonstration and pitch, see the companion `02_DEVPOST_MEDIA/` and `03_SUBMISSION_TEXT/` folders in the full submission package. [Judge quickstart](docs/JUDGES_START_HERE.md).

## License

MIT. The contributor should review this license before publishing the repository as open-source.
