# The position suite

`suite-base.jsonl`: 698 positions of the base game, one JSON object a line, which the sandbox's certification run plays
(README, "Certify your bot"): each from its position, your bot on each side in turn, up to the entry's next quiet
position. A bot with an engine of its own can also replay them itself to check its copy of the rules.

## An entry

- `id`: the entry's name (`hand-…` for hand-made positions, `g…` for positions harvested from games).
- `position`: the start, a **WPN** line (below); `after`: the position the entry's decisions reach.
- `steps`: the decisions and random outcomes in order. A decision: `side`, `decision` (the kind, §5), `fingerprint`
  (§4), `options` (each option's fields without `o` and `text`) and `choice` (the option taken). A random outcome:
  `{"random": {…}}`, as the `random_*` events (§8).
- `covers`: the tags the entry covers (cards offered and played, decision kinds, Hunt tiles, questions of the official
  rules).
- `scenario` (114 entries): `tag`, `from` and `side`: the certification run plays the first `from` decisions itself,
  then your bot answers that side's question (`new_game` says `scenario` and `played_for_you`). Every question a card
  asks, for the side it asks, is one: its tag is `question:CODE:SIDE:SHAPE` (`question:SC23:sh:whose-leadership-and-abilities-are-cancelled`:
  the question's words with names and numbers left out); an entry `…-qN` is a copy of the harvested entry `…` for one
  of them.

Every entry is played by the official rules (SPEC.md §9).

## WPN, the position notation (wpn1, base game)

One line, ASCII, fields separated by single spaces, always present, in this order. The first four are positional
(like FEN), the rest keyed (`key=value`) so a person can read them. Keys of the vocabulary (§6 of the protocol) are
used throughout, with short codes for the frequent ones .

```
wpn1 base-2e t1 R b=… k=… p=… f=… c=… d=… h=… cf=… cs=… r=… fl=… [end=…]
```

| Field | Meaning | Form |
|---|---|---|
| `wpn1` | notation version | |
| `base-2e` | the ruleset (`base-2e`; later `+lome`, `+council`, each adding fields) | as `rules` in `new_game` |
| `t1` | turn | `t` + number |
| `R` / `F.d` / `H` / `A:S` … | phase; for `A` the side to act (`F`/`S`); for `F` (its question open) the flags `d` declared, `g` Guide changed: `F`, `F.d`, `F.g`, `F.dg` | |
| `b=` | the board: every region with figures, a captured Settlement or a siege, in vocabulary order, `/`-separated | `slug[!C][#B]:item,item…` |
| `k=` | casualties per nation (the Free Peoples' units out of the game) | `go1.1/ro2`, or `-` |
| `p=` | the Political Track, the 8 nations in vocabulary order | steps to war 0–3, `a` if active: `3,3a,2,3,3,1a,1a,2a` |
| `f=` | the Fellowship: its region (on the Mordor Track too), the Mordor step if there, Progress, Corruption, hidden or revealed, the Guide, the other Companions in vocabulary order | `where[,m<step>],p<progress>,c<corruption>,h\|r,<guide>[,companions]` |
| `c=` | Characters out: eliminated `x:`, replaced `r:` | `x:bor,mer;r:str`, or `-` |
| `d=` | Action dice, Free Peoples `/` Shadow, in die order (options name dice by index) | one die each: see below |
| `h=` | Hunt tiles not in their starting place | `d:eye-1,3-2;y:elven-cloaks;x:…;p:…`, or `-` |
| `cf=`, `cs=` | Event cards of each side not in the deck, by zone: `h:` hand, `t:` on the table, `d:` the discard pile (face up), `x:` discarded face down | `cf=h:FC14,FS06;t:FS13;d:FC02,FS20;x:FC07`, or `-` |
| `r=` | Elven Rings, Free Peoples `/` Shadow; `*` used this turn | `3/0`, `2*/1` |
| `fl=` | turn flags: `h` the Shadow must hunt, `m` Messenger of the Dark Tower used, `f` the Fellowship acted (Mordor) | letters, or `-` |
| `end=` | only when the game is over: winner and how | `F:ring`, `S:corruption`, `S:military`, `F:military` |

**The board.** A region item is a nation's army, `<nation><regular>[.<elite>[.<leaders>[.<nazgul>]]]` with trailing
zeros dropped (nations `dw el go no ro is sa se`; `sa5.0.0.1` is five Regulars and a Nazgûl), or a Character on the
map by its code; the armies first in nation order, then the Characters in vocabulary order. `!F`/`!S` marks a
Settlement controlled by the side that did not start with it (only then: the default is its nation's side; `!-` one
controlled by neither), `#F`/`#S` a siege with that side besieged. Examples: `osgiliath!S:sa3` (Osgiliath captured,
three Sauron Regulars in it); `minas-tirith#F:go3.1.1,sa6.2.1,ara,wit` (Gondor besieged in Minas Tirith with
Aragorn, the Witch-king's army outside).

**Codes.** Characters: `gtg str bor leg gim mer per gtw ara gol wit sar mou` (the Ring-bearers, `rb`, are
implicit in `f=` and written only as its Guide, when no Companion is left).
Cards: side and deck and number, `FC14` = `fp-char-14`, `SS03` = `sh-strat-03`. Die faces: `C` Character, `A` Army,
`M` Muster, `X` Army/Muster, `E` Event, `W` Will of the West, `Y` Eye. A die: its face in upper case if available,
lower case if used (`_` a used die without a face), `?` not rolled yet, `+` before the face if it is in the Hunt Box
(`+Y` an Eye, `+C` a Free Peoples die used to move the Fellowship, `+?` a die there without a face). Hunt zones: `p`
pool, `s` set aside, `y` ready, `d` drawn, `x` removed; only tiles not in their starting zone are named (a standard
tile starts in the pool, a special tile set aside), in vocabulary order.

**What is derived, not written.** Reinforcements (the vocabulary's piece totals minus the board and the casualties),
the deck (every card not in another zone), Victory Points (from the Settlements' control), a Character not on the map,
in the Fellowship or in `c=` is not in play yet. One fact, one place: that is what makes the line unique.

**Not part of a position.** The order of the decks and of the Hunt Pool (draws are random), the generator's seed, the
history of the game (as in FEN, which also leaves out the repetition history).

**Canonical form and the position id.** A writer always produces the canonical form (fixed field order, regions and
cards in vocabulary order, defaults omitted, trailing zeros dropped); two positions are the same exactly when their
canonical lines are equal. The **position id** is the 64-bit FNV-1a of the line (as the decision fingerprint, §4 of the
protocol), 16 hex digits. A reader accepts only canonical lines in the suite; elsewhere it may accept any order.

A Companion of the starting Fellowship is always in play, eliminated (`x:`) or replaced (`r:`): `c=` is whole.
