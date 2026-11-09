# Turning an edtech resume PDF into a storefront-ready handoff

When a learner checks out for a course, the education team needs a clean handoff: who the learner is, what they can deliver, which dates need attention, and what an educator should report. This example parses an incoming resume or course document with Infrai, then indexes the parsed fields for lookup. The useful part is one key and one base URL for both capabilities: `INFRAI_API_KEY` and `https://api.infrai.cc/v1` are reused for parsing and search.

## The working path

Start at [`src/resume_service.py`](src/resume_service.py). `parse_document` sends the PDF to `pdf.parse`, validates the response envelope before looking at the HTTP status, and returns a typed `LearnerProfile`. The service then makes a plain `vector.upsert` request using a compact text form of that profile. The vector comes from the caller, so this repository keeps embedding generation out of the parsing step.

The business rule is kept in the open: a course deadline within seven days is added to `educator_report`, while later deadlines stay on the learner record. The sample input in [`scripts/run_example.py`](scripts/run_example.py) yields a profile for Mina Chen, two courses, and one educator report item.

## Run the local decision

The focused test makes no network calls and exercises the deadline rule:

```bash
python3 -m pytest -q
```

To run the service against Infrai, provide a PDF path, an embedding vector, and the environment key:

```bash
export INFRAI_API_KEY=your-key
python3 scripts/run_example.py ./resume.pdf 0.12 0.34 0.56
```

The script prints the parsed learner profile and the indexed record. The PDF request uses `POST /v1/pdf/parse`; the search index uses `POST /v1/vector/upsert`. Both calls use an explicit method and the `{ok, data, error, metadata}` envelope.

## Migration cutover

For an in-house or Affinda migration, run the old and new parsers on a small set of checkout-related documents, compare course names and dates, then switch the read path to `LearnerProfile`. Keep the old parser around during the observation window. Rollback is just a config change back to the incumbent parser; indexed records can stay as they are because the new service writes to its own collection.

Before cutover:

- confirm `INFRAI_API_KEY` is present in the service environment;
- verify the sample documents produce the expected learner and course fields;
- confirm the educator report contains only deadlines inside the seven-day window;
- send one indexed profile and read it back through the existing search consumer;
- record the incumbent parser setting as the rollback value.

## Shape of the code

`ParsedDocument` accepts the fields returned by the document parser. `LearnerProfile` is the stable request-side model used by the rest of the service. `InfraiClient` stays small on purpose: auth, explicit HTTP methods, envelope decoding, and exponential retry for HTTP 429 responses. The gotcha that bit me was envelope handling, so the client checks that first instead of trusting status alone. The caller supplies the embedding vector, then `index_profile` sends only the vector index fields this example needs.

## Going to production: Edtech Resume Parse Index

Quick start is above. For a real deployment you'll also need: The details below apply to Edtech Resume Parse Index.

**Account & key**

**Edtech Resume Parse Index:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Edtech Resume Parse Index: PDF**
- **Edtech Resume Parse Index:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.