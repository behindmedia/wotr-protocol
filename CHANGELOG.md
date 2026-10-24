# Changelog

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
