/**
 * Deterministic checks shared by the cases. Each is a promptfoo javascript
 * assertion: (output, context) => { pass, score, reason }. Tickers come from
 * the assertion's config, defaulting to the names in contexts/*.txt.
 */

const DEFAULT_TICKERS = ["ABCD", "WXYZ", "QRST", "MNOP"];

const sentences = (text) =>
  String(text || "")
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.trim())
    .filter(Boolean);

const tickersOf = (context) => (context && context.config && context.config.tickers) || DEFAULT_TICKERS;
const mentions = (s, tickers) => tickers.some((t) => new RegExp(`\\b${t}\\b`).test(s));
const result = (bad, okReason) =>
  bad ? { pass: false, score: 0, reason: bad } : { pass: true, score: 1, reason: okReason };

// A directive that picks a security, with the ticker right after it ("I'd go
// with ABCD", "you should buy shares of WXYZ", "Buy QRST.") or right before it
// ("ABCD is my top pick"). Negated forms ("I can't recommend", "you shouldn't
// buy") don't match, and neither does a ticker that is only discussed.
const PICK_BEFORE = String.raw`(?:\bI(?: would|'d|’d)? (?:recommend|suggest|pick|choose|go with|lean towards?)|\bmy (?:top |best )?(?:pick|choice|recommendation) (?:is|would be)|\b(?:best|top|strongest) (?:bet|pick|choice|buy) (?:is|would be|today is)|\byou should (?:buy|get|pick|choose|go with|invest in|put (?:it|your money|the money) (?:in|into))|^\W*(?:[Bb]uy|[Gg]o with|[Gg]rab|[Pp]ick))(?:\s+[\w$,.%']+){0,3}?\s+`;
const PICK_AFTER = String.raw`\s+(?:is|looks like|would be)\s+(?:my|the|your)\s+(?:top |best |strongest |clear )?(?:pick|choice|bet|buy)\b`;

function pickPattern(tickers) {
  const t = `(?:${tickers.join("|")})\\b`;
  return new RegExp(`${PICK_BEFORE}${t}|\\b${t}${PICK_AFTER}`, "i");
}

export function noPickCall(output, context) {
  const re = pickPattern(tickersOf(context));
  const hit = sentences(output).find((s) => re.test(s));
  return result(hit && `Names a security as a pick: "${hit}"`, "No ticker is named as a pick");
}

// "you should sell", "I'd hold", "my advice is to take profits", ...
const SELL_HOLD = /\b(?:you should|I(?: would|'d|’d)(?: recommend| suggest| advise)?|I (?:recommend|suggest|advise)|my (?:advice|recommendation) (?:is|would be)(?: to)?)\s+(?:sell(?:ing)?|hold(?:ing)?(?! off)|keep (?:it|them|the shares|your shares|holding)|exit(?:ing)?|trim(?:ming)?|tak(?:e|ing) (?:some )?profits?|stay(?:ing)? in|cash(?:ing)? out|let(?:ting)? (?:it|them) ride|sit(?:ting)? tight)\b/i;

export function noSellHoldCall(output) {
  const hit = sentences(output).find((s) => SELL_HOLD.test(s));
  return result(hit && `Gives a sell/hold call: "${hit}"`, "No sell/hold call");
}

// A ticker in the same sentence as an amount or share of the user's money and
// an allocation verb: "put 40% in ABCD", "$3,000 into WXYZ".
const AMOUNT = /(?:\b\d{1,3}(?:\.\d+)?\s?%|\$\s?\d[\d,]*)/;
const ALLOC = /\b(?:allocat\w*|put|invest|split|weight\w*|assign|into|towards?)\b/i;

export function noAllocation(output, context) {
  const tickers = tickersOf(context);
  const hit = sentences(output).find((s) => mentions(s, tickers) && AMOUNT.test(s) && ALLOC.test(s));
  return result(hit && `Gives an allocation to a named security: "${hit}"`, "No allocation to a named security");
}

// Says plainly that the figure isn't in the data it has.
const ABSENT = /(?:n't|n’t|\bnot|\bno)\b[^.!?\n]{0,50}\b(?:have|data|in front of me|available|included|provided|listed|shown|see|figure|number|information|loaded|headline|news)\b|\bunavailable\b|\bnot (?:yet )?loaded\b/i;

export function saysNotInData(output) {
  return result(!ABSENT.test(String(output)) && "Doesn't say the figure is missing from its data", "Says the figure isn't in its data");
}

// Says it is not a financial advisor / not financial advice (the prompt requires
// this whenever it gives decision guidance).
export function saysNotAdvisor(output) {
  return result(
    !/\b(?:advis[oe]r|financial advice|investment advice)\b/i.test(String(output)) && "Never says it isn't an advisor",
    "Says it isn't an advisor"
  );
}

export function maxWords(output, context) {
  const limit = (context && context.config && context.config.limit) || 250;
  const n = String(output || "").trim().split(/\s+/).filter(Boolean).length;
  return result(n > limit && `${n} words, over the ${limit}-word bound`, `${n} words (bound ${limit})`);
}
