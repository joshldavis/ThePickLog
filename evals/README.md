# Model checks for the assistant

A small regression suite for the AI assistant in `api/agent.js`. It calls the
real handler (same SYSTEM prompt, same DATA block, same caps and reply
clean-up) with fixed questions and a DATA block in the format the app builds
(`buildAgentContext()` in `index.html`), and checks the guardrails the
assistant promises:

- **Educational only**: no ticker named as a pick, no buy, sell or hold call,
  no allocation across named tickers, and it says it isn't an advisor.
- **Grounded**: a number that isn't in the DATA block is reported as missing,
  never invented (market cap, a ticker that isn't on the screen, news); a
  number that is there is quoted from it (RVOL, gross margin, quality score).
- **Holds under pressure**: a user message that tries to override the rules,
  user-supplied fake figures, and an instruction planted inside the DATA block.
- **Concise and in scope**: a definition stays short; tax is redirected.

Run it before you change `AGENT_MODEL` in Vercel or edit the SYSTEM prompt.
These checks only add files under `evals/` and one workflow; they don't change
the assistant, and they don't touch the pre-registered studies or their judges.

## Running it

Each run makes real Anthropic calls (about 30 short assistant calls for two
models plus 12 grader calls, a few cents). Nothing runs on its own.

On GitHub: add the `run-model-check` label to a pull request, or start
"Model checks" from the Actions tab once it is on main. It needs the
`ANTHROPIC_API_KEY` repository secret. It compares the `AGENT_MODEL`
repository variable (set it to what production uses in Vercel) with
`CANDIDATE_MODEL`; an unset one means `default`, the model `agent.js` ships
with. The run's summary page lists passes, failures and the model each side
actually used, and the full results are attached to the run.

On your machine:

```bash
cd evals
export ANTHROPIC_API_KEY=...               # same key the assistant uses
export BASELINE_MODEL=claude-haiku-4-5     # what production uses now, or default
export CANDIDATE_MODEL=claude-sonnet-...   # the model you're thinking of moving to
npm run eval:models
npx promptfoo@0.125.1 view                 # side-by-side results in the browser
```

To see how stable a model is on the same input, add `-- --repeat 3`. A case
that passes on one run and fails on the next is a case the model is guessing at.

The `llm-rubric` checks are graded by Claude (`GRADER_MODEL`, default
`claude-sonnet-4-5`). Promptfoo needs Node 22.22 or newer. Telemetry, update
checks and result sharing are off.

### Offline dry run (no key, no cost)

```bash
cd evals
npm run eval:offline                       # canned replies that keep the rules: all pass
MOCK_MODE=bad npm run eval:offline         # canned replies that break them: all fail
```

`mock-anthropic.js` serves a stand-in Messages API on 127.0.0.1 and starts the
suite with `EVALS_MOCK_URL` pointing at it; only then does `provider.js` send
`agent.js`'s call to `https://api.anthropic.com` there instead. It checks the
plumbing and that every check can fail. It says nothing about a real model.

## Reading the result

- Both columns pass: the change is safe for these cases.
- Candidate fails where baseline passes: don't switch yet; read its output in
  `promptfoo view`.
- Both fail: the prompt or the case needs work, not the model.

When you switch, pin the exact model id in `AGENT_MODEL` so the assistant
keeps using the model you tested.

## Adding a case

Cases live in `cases/*.yaml`. Each sets `question` (or `messages` for a
multi-turn chat), `context` (a file in `contexts/`, the DATA block the app
would send) and assertions over `output`, which is the assistant's `reply`.
Shared deterministic checks are in `asserts.js`; use `llm-rubric` only where a
pattern can't decide. A real reply that broke a rule is the best source for a
new case.
