"""Conservative local checks on free-form wording repair.

These checks catch observable fact changes. They do not prove semantic equivalence;
the original and the interpretation must stay available for inspection/evaluation.
"""
from collections import Counter
from difflib import SequenceMatcher
import re
import sys
import unicodedata
from pathlib import Path

from backend.classifier.contracts import validate_request

_TYPING_PATH = str(Path(__file__).resolve().parents[1] / "dataset/pipelines/item10")
if _TYPING_PATH not in sys.path:
    sys.path.insert(0, _TYPING_PATH)
from typing_repair import matching_text, ANCHORS

WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
FUNCTION_WORDS = set("""a an the is are was were be been being am i me my mine we us our
    you your yours he him his she her hers they them their it its this that these those
    and or but for to of on in at by from with as do does did can could would should
    will shall may might have has had what how when where why which who please thank
    thanks hello hi po opo ho ako ko akin kami namin tayo natin ikaw ka mo kayo ninyo
    siya nya niya sila nila ang mga ng nang sa na ni kay ay ba naman lang lamang
    yung yong iyong ito iyon yan dito doon dyan rin din daw raw at o pero kasi dahil
    kung kapag para mula anu ano paano pano bakit saan kailan sino alin magkano
    pwede puwede maaari gawin gagawin kong naming kanyang kanilang aking mong itong
    niyang naman pa pala yungpong anong hindi hinde inde ndi hndi hnd nd di d not no never
    without cannot can't didn't doesn't don't isn't wasn't aren't weren't wont won't
    wala walang walangpong already still yet just also about then now help need want
    sabihin question concern problem issue tanong tulong paki pakisuyo salamat""".split())
NEGATIONS = set("hindi hinde inde ndi hndi hnd nd di not no never without cannot can't didn't doesn't don't isn't wasn't aren't weren't won't wont wala walang".split())
NEGATIVE_SHORTHAND = {"d"}
AGENCIES = set("dti dole sss gsis nlrc nwpc nbi pnp bir dole sena dojh".split())
# Extra category/domain facts must have a spelling counterpart in the original.
FACT_WORDS = set("""private pribado government gobyerno gobierno govt municipal public
    kasambahay household domestic overseas ofw seafarer union banking bank bangko
    insurance insurer criminal fraud privacy loan pension salary sahod sweldo wages
    employer employee refund warranty overtime termination dismissed fired legal
    illegal court police paid unpaid""".split())
PRONOUNS = {
    "first_singular": set("ako ko akin aking kong i me my mine".split()),
    "first_plural": set("kami namin naming tayo natin we us our".split()),
    "second": set("ikaw ka mo mong kayo ninyo you your yours".split()),
    "third": set("siya niya nya niyang sila nila kanyang kanilang he him his she her hers they them their".split()),
}
NUMBER = re.compile(r"(?<![\w])\d+(?:[,.]\d+)*(?![\w])", re.UNICODE)
LITERAL = re.compile(r"https?://[^\s]+|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|[\"“]([^\"”\n]+)[\"”]")


def words(text):
    return [m.group().casefold().replace("’", "'") for m in WORD.finditer(text)]


def spelling_key(word):
    word = unicodedata.normalize("NFKD", word.casefold())
    if any(c.isalpha() for c in word):
        word = word.translate(str.maketrans("013457", "oieast"))
    for old, new in (("ph", "p"), ("f", "p"), ("v", "b"), ("c", "k"), ("q", "k")):
        word = word.replace(old, new)
    word = re.sub(r"(.)\1+", r"\1", word)
    word = re.sub(r"(?<=[aeiou])h$", "", word)
    if word.endswith("ng") and word[:-2] in FUNCTION_WORDS:
        word = word[:-2]
    return word


def skeleton(word):
    word = spelling_key(word)
    return re.sub(r"(.)\1+", r"\1", re.sub(r"[aeiouyw\d\W_]", "", word))


def spelling_related(left, right):
    left, right = spelling_key(left), spelling_key(right)
    if left == right:
        return True
    if any(left in group and right in group for group in PRONOUNS.values()):
        return True
    # Flexible vowel removal / phonetic spelling; not a decoding dictionary.
    a, b = skeleton(left), skeleton(right)
    if min(len(left), len(right)) <= 3 and a != b:
        return False
    if len(a) >= 3 and a == b and max(len(left), len(right)) <= 3 * min(len(left), len(right)):
        return True
    if len(a) >= 2 and a == b and (left in FUNCTION_WORDS or right in FUNCTION_WORDS):
        return True
    if len(left) == len(right) == 3:
        return sum(a != b for a, b in zip(left, right)) <= 1
    if min(len(left), len(right)) < 3:
        return False
    return SequenceMatcher(None, left, right, autojunk=False).ratio() >= .72


def supported(word, source):
    return any(spelling_related(word, candidate) for candidate in source)


def negative_count(tokens):
    count = 0
    for index, word in enumerate(tokens):
        # In this narrow English auxiliary pattern, nd expands to need.
        # Keep nd negative elsewhere; do not infer this from a label/reference.
        need_pattern = (word == "nd" and index >= 2 and index + 1 < len(tokens)
                        and tokens[index - 2] in {"do", "does", "did"}
                        and tokens[index - 1] in {"i", "you", "we", "they", "he", "she"}
                        and tokens[index + 1] == "to")
        if need_pattern:
            continue
        count += (word in NEGATIONS or (word not in FUNCTION_WORDS and skeleton(word) in {"hnd", "nd", "wl", "wlng"})
                  or bool(re.match(r"^(?:hindi|hndi|ndi)(?=[a-z]{4,})", word)))
    return count


def boundary_support(before, after, *, exact_only=False):
    """Locate split/merged spans without introducing a synonym dictionary.

    Each side has at most three words and at least one side is a single token.
    Joined spelling must be identical or share the full consonant skeleton;
    arbitrary approximate matches cannot license new words/facts.
    """
    old_supported, new_supported = set(), set()
    for i in range(len(before)):
        for n in (1, 2, 3):
            if i + n > len(before):
                continue
            old = spelling_key("".join(before[i:i + n]))
            for j in range(len(after)):
                for m in ((2, 3) if n == 1 else (1,)):
                    if j + m > len(after):
                        continue
                    new = spelling_key("".join(after[j:j + m]))
                    same_skeleton = (len(skeleton(old)) >= 3 and skeleton(old) == skeleton(new)
                                     and max(len(old), len(new)) <= 2 * min(len(old), len(new)))
                    if old == new or (same_skeleton and not exact_only):
                        old_supported.update(range(i, i + n))
                        new_supported.update(range(j, j + m))
    return old_supported, new_supported


def names(text):
    matches = list(WORD.finditer(text))
    found = []
    uppercase_sentence = sum(m.group().isupper() for m in matches) > .7 * max(1, len(matches))
    for i, match in enumerate(matches):
        value = match.group()
        lower = value.casefold()
        if lower in FUNCTION_WORDS or lower in FACT_WORDS:
            continue
        marker = i > 0 and matches[i - 1].group().casefold() in {"si", "ni", "kay", "named", "mr", "ms", "dr"}
        interior_capital = (i > 0 and value[:1].isupper()
                            and not re.search(r"[.!?]\s*$", text[:match.start()]))
        acronym = len(value) >= 2 and value.isupper() and not uppercase_sentence
        if marker or interior_capital or acronym:
            found.append(lower)
    return Counter(found)


def validate_rewrite(original, payload):
    if type(payload) is not dict or set(payload) != {"status", "normalized_question"}:
        raise ValueError("invalid_normalization_contract")
    status, text = payload["status"], payload["normalized_question"]
    if type(status) is not str or status not in {"unchanged", "normalized", "unclear"} or type(text) is not str:
        raise ValueError("invalid_normalization_contract")
    if status != "normalized":
        if text:
            raise ValueError("unexpected_rewrite")
        return original, []
    validate_request({"question_text": text})
    if not text.strip() or text == original or len(text) > max(160, 3 * len(original)):
        raise ValueError("invalid_rewrite_length")
    before, after = words(original), words(text)
    source_anchors = Counter(w for w in words(matching_text(original)) if w in ANCHORS)
    proposed_anchors = Counter(w for w in words(matching_text(text)) if w in ANCHORS)
    if source_anchors - proposed_anchors:
        raise ValueError("scope_anchor_changed")
    proposed_matching_words = words(matching_text(text))
    for token in before:
        expanded = words(matching_text(token))
        if len(expanded) > 1 and any(w in ANCHORS for w in expanded):
            if not any(proposed_matching_words[i:i + len(expanded)] == expanded
                       for i in range(len(proposed_matching_words) - len(expanded) + 1)):
                raise ValueError("scope_anchor_changed")
    if len(before) > 400 or len(after) > 600:
        raise ValueError("normalization_word_limit")
    if NUMBER.findall(original) != NUMBER.findall(text):
        raise ValueError("numeric_facts_changed")
    for match in LITERAL.finditer(original):
        if match.group() not in text:
            raise ValueError("literal_fact_changed")
    old_counts, new_counts = Counter(before), Counter(after)
    old_boundary, new_boundary = boundary_support(before, after)
    # Removing/adding a repeated syllable can change Filipino verb aspect.
    # This is distinct from extra repeated characters used as typing noise.
    for source, target, source_counts, target_counts in [(before, after, old_counts, new_counts),
                                                         (after, before, new_counts, old_counts)]:
        for word in source:
            if source_counts[word] <= target_counts[word]:
                continue
            for match in re.finditer(r"([bcdfghjklmnpqrstvwxyz][aeiou])\1", word):
                shortened = word[:match.start()] + word[match.start() + 2:]
                if shortened in target and target_counts[shortened] > source_counts[shortened]:
                    raise ValueError("syllable_reduplication_changed")
    # Morphological polarity is not captured by counting standalone 'not'.
    for word in before:
        collapsed = re.sub(r"(.)\1+", r"\1", word)
        for candidate in after:
            other = re.sub(r"(.)\1+", r"\1", candidate)
            if (new_counts[candidate] > old_counts[candidate] and
                    any(other == prefix + collapsed or collapsed == prefix + other for prefix in ["un", "non", "dis"])):
                raise ValueError("lexical_polarity_changed")
    # A tripled-letter token can lose repeated characters, but cannot acquire
    # a new syllable/aspect or change a consonant under the guise of cleanup.
    for word in before:
        if re.search(r"(.)\1{2,}", word):
            collapsed = re.sub(r"(.)\1+", r"\1", word)
            if not any(collapsed == re.sub(r"(.)\1+", r"\1", candidate) for candidate in after):
                raise ValueError("repeat_repair_changed_word")
    for agency in AGENCIES:
        if old_counts[agency] != new_counts[agency]:
            raise ValueError("agency_changed")
    for name, count in names(original).items():
        if new_counts[name] < count:
            raise ValueError("name_changed")
    participant_before = before + ["ko" for w in before if w in {"q", "aq"}]
    participant_before += ["kami" for w in before if w in {"kmi", "kme"}]
    _, exact_new_boundary = boundary_support(before, after, exact_only=True)
    for pronouns in PRONOUNS.values():
        before_known = bool(pronouns.intersection(participant_before))
        after_known = bool(pronouns.intersection(after))
        variant_support = any(spelling_related(w, p) for w in before if w not in FUNCTION_WORDS for p in pronouns)
        variant_support = variant_support or any(i in exact_new_boundary and word in pronouns for i, word in enumerate(after))
        if before_known and not after_known or after_known and not before_known and not variant_support:
            raise ValueError("participant_changed")
    # d/q/aq are ambiguous outside context. Permit their established pronoun or
    # negation expansions, but never remove an existing explicit negation.
    if negative_count(after) < negative_count(before):
        raise ValueError("negation_removed")
    extra_negations = negative_count(after) - negative_count(before)
    if extra_negations > sum(w in NEGATIVE_SHORTHAND for w in before):
        raise ValueError("negation_added")
    old_content = [w for w in before if w not in FUNCTION_WORDS and not w.isnumeric()]
    new_content = [w for w in after if w not in FUNCTION_WORDS and not w.isnumeric()]
    # Allow split/merged words. Both directions are checked so a rewrite cannot
    # discard an unfamiliar second concern merely to get a supported label.
    old_joined = before + ["".join(before[i:i + n]) for n in (2, 3) for i in range(len(before) - n + 1)]
    new_joined = after + ["".join(after[i:i + n]) for n in (2, 3) for i in range(len(after) - n + 1)]
    for word in old_content:
        # Compressed words can retain repeated consonants from a lost syllable
        # (mnnalo -> mananalo). Do not silently collapse that signal to manalo.
        if (len(re.findall(r"[aeiou]", word)) <= 2
                and re.search(r"([bcdfghjklmnpqrstvxz])\1(?=[a-z])", word)
                and not re.search(r"(.)\1{2,}", word)):
            outline = re.sub(r"[aeiouyw\d\W_]", "", word)
            candidates = [w for w in new_joined if skeleton(word) == skeleton(w)]
            if candidates and not any(re.sub(r"[aeiouyw\d\W_]", "", w) == outline for w in candidates):
                raise ValueError("syllable_reduplication_changed")
    shorthand = {"q", "aq", "d", "po", "gn2", "d2"}
    for index, word in enumerate(before):
        if word not in old_content or index in old_boundary:
            continue
        if (len(word) <= 3 and word not in shorthand and spelling_key(word) not in FUNCTION_WORDS
                and word not in after and not any(spelling_related(word, candidate) for candidate in new_content)):
            raise ValueError("ambiguous_short_content_replaced")
        if word not in shorthand and not supported(word, new_joined):
            raise ValueError("original_concern_not_preserved")
    for index, word in enumerate(after):
        if word not in new_content or index in new_boundary:
            continue
        if word not in shorthand and not supported(word, old_joined):
            raise ValueError("unsupported_new_content")
    for fact in FACT_WORDS.intersection(after):
        if not supported(fact, before) and not any(i in new_boundary and word == fact for i, word in enumerate(after)):
            raise ValueError("unsupported_new_fact")
    # A character-level diff is an audit trail, not provider-chosen offsets.
    edits = [{"start": a, "end": b, "original": original[a:b], "replacement": text[c:d]}
             for op, a, b, c, d in SequenceMatcher(None, original, text, autojunk=False).get_opcodes() if op != "equal"]
    return text, edits
