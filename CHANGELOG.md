# Changelog

## 0.2, 2026-11-25: every card question a scenario

The protocol is unchanged. The position suite (`positions/suite-base.jsonl`): 698 entries, 114 scenarios. Every
question an Event card asks is now a scenario of its own, for the side it asks (`question:CODE:SIDE:SHAPE`): a card
may ask several (The Ringwraiths Are Abroad's Event and its Combat card, Words of Power), and a bot meets one in an
ordinary entry only if it makes the same moves. Found when a certified bot still answered some of them with a default
in a long match. The sandbox's certification run plays the new suite from its next update.

## 0.2, 2026-11-23: the official rules and certified bots

- **The official rules, no house rules** (§9): a referee that says `"official_rules": true` in `new_game` offers every
  option the rulebook allows (`no_effect` marks those that change nothing) and asks every question it asks: the Leader
  re-roll (`LEADER_REROLL`, §5), declining a "may draw" (`draw` with `skip`), Mighty Attack's Companion, the Guide
  after a Hunt separation, every reveal path (`reveal`'s `strongholds`), the Voice of Saruman's Settlements when
  Regulars are short (`voice_of_saruman`'s `regions`), and the passes on a hidden hand (`hidden_passes`).
- **A question that changes nothing is answered by the referee**: a `choice` event with `for_you`, no `decide` (§8).
- **The Lidless Eye's options** carry `die` and `face` (`count` kept, §5). Conformance game 202: three fingerprints
  follow; every choice, the result and the final views are unchanged. The other six games are unchanged.
- **Certified bots**: the sandbox's certification run, `?certify=base` (games against `greedy` and `random`, the
  position suite's 594 entries on each side, 15 scenarios) and its verdict (README, "Certify your bot"). A game from a
  position (`start`, `suite_entry`, `view`) and a scenario (`scenario`, `played_for_you`), §9. The suite and the
  position notation (WPN) are in [`positions/`](positions/).

## 0.2, 2026-11-20: the sandbox

The protocol is unchanged. A test referee for the site's bot testers, `wss://sandbox.wotr.behindmedia.com/referee`,
with sandbox keys: greedy, random or self-play opponents, up to 1000 games, clocks from 20 ms, fixed seeds, results and
logs per key (README, "A sandbox to test your bot"); the `options` message's `match` object carries `sandbox` (true).
The hosted referee's matches are between two bots; our greedy bot is in the sandbox.

## 0.2, 2026-11-18: bot tournaments

The protocol is unchanged. TOURNAMENTS.md describes the site's bot tournaments: a bot is a Docker image that reads
`WOTR_REFEREE_URL` and `WOTR_SEAT_TOKEN` from its environment and plays one game; the `options` message's `match`
object carries `tournament` (true), `game_number`, `games`, `clock_ms`, `max_turns`, `timeouts_forfeit` (1),
`paired_seeds` and `frozen_between_decisions` (the bot is paused between its decisions; the clock starts after the
thaw).

## 0.2, 2026-11-18: game logs

The protocol is unchanged. §10 now defines the **protocol log** a referee keeps of each game ("Game logs"): JSON
Lines, one message a line with `t`, `side`, `dir` and the message as sent in `line`; a one-seat log; a zip of several
games with `games.json`. This is the format referees already wrote (matches, hosted bots' games); it is now the
standard for downloads of matches' and tournaments' games.

## 0.2, 2026-11-17: Worn with Sorrow and Toil's discard face down

The protocol is unchanged. The card the Free Peoples discard from their hand to "Worn with Sorrow and Toil" is
discarded face down, as the rules' discards from the hand are: it no longer shows in the public `discards` of either
view, but in `discarded_face_down` (and the opponent's `opponent_discarded_face_down` count). Conformance game 302:
its `final_views` follow (two such cards move); every choice and fingerprint is unchanged. The other six games are
unchanged.

## 0.2, 2026-11-15: an Elven Ring on a Will of the West, and Fire and Shadow past the Balrog

The protocol is unchanged. The referee follows two rules corrections. An Elven Ring may turn a Will of the West die
into another result while "The Day Without Dawn" may still come (that card discards unused Will of the West dice), so
`elven_ring` options with `"from":"WILL_OF_THE_WEST"` are offered again in those games. In Lords of Middle-earth, a
reveal whose way must pass the Balrog in Moria draws the Balrog's tile ("Fire and Shadow") as well as Moria's,
unless "Balrog of Moria" is on the table to make the way through Moria a choice. The conformance games follow:
`game-101`, `game-102`, `game-201` and `game-301` keep their choices with new option numbers and fingerprints
(each earlier fingerprint is the new options without the Ring's Will of the West changes), `game-103` and `game-302`
are recorded anew from the same seeds (both won by the Free Peoples (Ring), in turns 20 and 24); `game-202` is
unchanged.

## 0.2, 2026-10-31: the price of forcing a card off is discarded face down

The two cards the Shadow pays to force "A Power too Great" or "The Power of Tom Bombadil" off the table are discarded
face down, as the rules' discards from the hand are: the Free Peoples' `choice` event shows that `use_die` option
without `pay` and `o`, with `"hidden":true`, and `die_used` has no `pay` for them (SPEC §8). A bot that reads `pay`
from the opponent's choice must expect it to be absent. The referee also no longer asks which Companion forfeits his
Leadership to "Mighty Attack" (the lowest one goes), and no longer offers "Daring Defiance" under "The White Rider".
`politics_advanced` may carry `"back":true` (a step away from war, "Stormcrow").
Conformance games 201, 202 and 301: their `final_views` follow (the paid cards are face down); every choice and
fingerprint is unchanged.

## 0.2, 2026-10-31: no Event card without an effect

The protocol is unchanged. The referee no longer offers to play an Event card that would change nothing, also when
playing it would draw a card (Gandalf the Grey as the Guide, the Palantír). The conformance games follow: `game-101`,
`game-102` and `game-201` keep their choices with new option numbers and fingerprints, `game-103`, `game-202` and
`game-302` are recorded anew from the same seeds (`game-103` now a Ring win, `game-202` ends at the turn cap).

## 0.2, 2026-10-29: Vilya and a changed Will of the West

An added field, so 0.2 stays: a `KEEPER_RING` option for Vilya on a Will of the West die that was changed into another
result (as the War of the Ring Almanac, Expansions, rules) carries `face`, one option per result it may be kept as
(e.g. `EVENT` and `CHARACTER` after a Character card). Every other Keeper Ring option is unchanged. Conformance
game-301's decision fingerprint at step 51 follows.

## 0.2 (2026-10-24)

Rulesets and the expansion Lords of Middle-earth, with and without its Council of Rivendell (SPEC.md §13).
**Backwards compatible**: everything of 0.1 is unchanged for the base game, byte for byte. A bot without `rulesets`
in its `hello` (every 0.1 bot) plays the base game and is never given another; a 0.2 referee accepts any
`wotr-bot/0.x` bot.

- `hello`: the protocol says `wotr-bot/0.2`; a bot may declare `"rulesets": ["base", "lome", "lome:council"]`.
- `new_game` of an expansion's game: `"variant": ["lome"]` or `["lome", "council"]` and `"ruleset"` (the canonical
  key); `rules` stays `base-2e`.
- The vocabulary (`vocabulary/vocabulary-0.2.json`, a superset of 0.1's): the expansion's cards keyed `lome-…`, its
  characters and the versions of base characters, the special dice and their faces (`CARD_DRAW`, `USE_BALROG`), the
  Elven Rings (`ring`), the Sméagol tiles, the Council's Action tokens, the decision kinds and die actions.
- Five decision kinds: `SPECIAL_DIE`, `KEEPER_RING`, `SETUP_VERSION`, `SETUP_GUIDE`, `COUNCIL`; new options in
  `ACTION` (`use_token`, the special dice's `special_die`, the new die actions), `EXTEND_SIEGE` (`evil_knowledge`)
  and `CARD_CHOICE` (`ability`); `ring` on `elven_ring` and `force_discard`.
- A secret choice: a Companion's version (`SETUP_VERSION`), shown to the opponent only as the base Companion until
  the game reveals it (`version_revealed`).
- Events: `random_special_die` among the random outcomes; the expansion's board events.
- The view: a `lome` part in an expansion's game only.
- Conformance: four games of Lords of Middle-earth (`game-201`, `game-202`; with the Council `game-301`, `game-302`);
  the three base games are unchanged.
- Online play against people on the hosted site (SPEC.md §14, in use since 2026-10-22): bot keys, `seek`, the `game`
  and `correspondence` clocks, coming back after a drop; bots are offered games of the rules they declare.
- The example bot (`examples/python/random_bot.py`) speaks 0.2: it declares `"rulesets": ["base", "lome",
  "lome:council"]` (fewer with `--rulesets`), logs each game's ruleset and says version `0.2`.

## 0.1 (2026-10-21)

The first draft, as implemented by the reference referee: the session, decisions with option lists and fingerprints,
the 26 decision kinds of the base game, the vocabulary, the view, the events, conformance games and matches; the
hosted referee (SPEC.md §12).
