# WotR Bot Protocol (draft 0.1)

A text protocol that lets computer opponents for **War of the Ring, Second Edition** (base game) play each other, and
people, whatever language or rules engine each is written in. Draft for discussion with the authors of other War of the
Ring bots (2026-10-21); nothing here is final.

## 1. Why this shape

Bridging bots by running two rules engines in lock step, translating every step, has been tried (between three War
of the Ring bots, 2026-10). It works, but most of the effort goes into keeping two engines in agreement: map borders, the order of steps,
how coarse an action is, card edge cases. Every difference becomes a desync.

This protocol avoids that: **one referee holds the rules; bots only choose.**

- The **referee** is any rules engine that conforms to this protocol. It runs the game, rolls every die, draws every
  card and tile, and at each decision sends the deciding bot **its view of the position and the list of legal
  options**, written in a shared vocabulary.
- A **bot** answers with **one option id**. It never needs to agree with the referee's rules; it only has to read the
  view and the options. A bot that searches with its own engine builds its own state from the view (and may follow the
  event stream), and its engine's opinion about legality doesn't matter: the referee's list is the truth.

This is how chess (UCI) and Go (GTP) engines are run against each other, adapted to hidden information and chance.

## 2. Transport

- **JSON Lines**: one JSON object per line, UTF-8, `\n`-terminated, no pretty-printing.
- **Local**: the referee starts the bot as a child process and talks over its stdin and stdout. Anything the bot writes
  to stderr is a log, never protocol.
- **Remote**: the same messages over a WebSocket (one message per frame) or a TCP stream (one per line).
- Every message has a `"type"`. Requests from the referee that need an answer carry an `"id"`; the answer repeats it.
- Unknown fields are ignored (forward compatibility). Unknown message types get an `error` answer if they carry an
  `id`, and are ignored otherwise.

## 3. The session

```
referee → bot   {"type":"hello","protocol":"wotr-bot/0.1","referee":"wotr-referee 2026.10","id":1}
bot → referee   {"type":"hello","id":1,"protocol":"wotr-bot/0.1","name":"ExampleBot","version":"1.0","author":"…",
                 "options":[{"name":"sims","type":"int","default":300,"min":1,"max":100000}]}
referee → bot   {"type":"options","values":{"sims":300}}
referee → bot   {"type":"new_game","id":2,"game":"g-87000005","side":"SHADOW","rules":"base-2e","variant":[],
                 "seed_bot":12345,"clock":{"kind":"per_decision","ms":10000}}
bot → referee   {"type":"ready","id":2}
… decisions and events …
referee → bot   {"type":"game_over","game":"g-87000005","winner":"FREE_PEOPLES","how":"RING_DESTROYED","turn":9}
referee → bot   {"type":"quit"}
```

- **One game at a time per connection** in 0.1. A match runner opens one connection per bot per game, or reuses it.
- `seed_bot` is the bot's own seed, for reproducible matches. The game's seed is **never** sent: it would reveal the
  dice and the decks.
- `rules`: `"base-2e"` is the Second Edition base game with the published errata (see §9). `variant` lists optional
  rules both sides agreed on; empty in 0.1.

## 4. Decisions

```
referee → bot   {"type":"decide","id":17,"game":"g-87000005","decision":{
                   "kind":"ACTION","prompt":"Choose an Action die and what to do with it",
                   "options":[
                     {"o":0,"kind":"use_die","die":2,"face":"ARMY","action":"move_armies"},
                     {"o":1,"kind":"use_die","die":2,"face":"ARMY","action":"attack"},
                     {"o":2,"kind":"use_die","die":4,"face":"EVENT","action":"play_card","card":"sh-strat-07"},
                     {"o":3,"kind":"pass"}],
                   "fingerprint":"3f9a…"},
                 "view":{…},
                 "clock":{"left_ms":10000}}
bot → referee   {"type":"choice","id":17,"o":1,"fingerprint":"3f9a…","info":{"visits":2400,"value":0.61}}
```

- **One decision = one question with a closed list of options.** The bot answers with the option's `o`. Options are
  described in the shared vocabulary (§6), so a bot can understand them, but it never has to construct one.
- **`fingerprint`**: a hash the referee computes over the canonical text of the option list; the bot echoes it so the
  referee can detect an answer to a stale question. A bot may ignore it.
- **Atomic steps.** Compound actions are asked step by step, in the rulebook's order, e.g. an Army move is: the die and
  the action (`ACTION`), then which Army from where to where (`ARMY_MOVE`), then which units go if not all
  (`ARMY_SELECTION`), then the next Army or the end (`ARMY_MOVE` again). This is the one place bots must meet the
  referee's granularity, so the kinds are fixed by this specification (§5), not by an engine.
- **`info`** (optional): anything the bot wants logged (visits, value, principal line). The referee records it and
  never shows it to the opponent.
- **Time**: `clock` says how much time is left for this decision (`per_decision`) or for the whole game (`game`, with
  an increment). A bot that misses the deadline gets a `timeout` notice; the referee then plays option 0 (or forfeits
  the game, if the match rules say so).
- **Illegal or unknown answers**: the referee answers `{"type":"error","id":17,"code":"illegal_option"}` and asks again,
  once; a second illegal answer forfeits the game.

## 5. Decision kinds (0.1)

| Kind | The question | Options carry |
|---|---|---|
| `FELLOWSHIP_PHASE` | declare the Fellowship, enter Mordor, change the Guide, or done | `declare` + `region`; `enter_mordor`; `guide` + `character`; `done` |
| `HUNT_ALLOCATION` | how many dice into the Hunt Box (Shadow) | `count` |
| `ACTION` | which die, and which action with it (or pass, or skip a die) | `die`, `face`, `action`, plus `card`, `character`, `nation`, `region` as the action needs |
| `ARMY_MOVE` | which Army moves where, or end the move | `from`, `to`, `all` (bool), or `end` |
| `ARMY_SELECTION` | how many of each unit kind move | `nation`, `unit`, `count` |
| `CHOOSE_ATTACK` | which attack (from where, which region, with or without Leader) | `from`, `to`, `with_leader` |
| `FIELD_OR_SIEGE` | the defender of a Stronghold: field battle or withdraw | `field` / `siege` |
| `COMBAT_CARD` | a Combat card for this round, or none | `card` or `none` |
| `CASUALTY` | which unit to remove or reduce for a hit | `nation`, `unit`, `effect` (`remove` / `reduce`) |
| `REMOVE_EXCESS_UNIT` | which unit leaves an overfull region or siege | `nation`, `unit` |
| `CEASE_ATTACK` | the attacker continues or ceases | `continue` / `cease` |
| `RETREAT` | the defender retreats where, or stands | `region` or `stand` |
| `EXTEND_SIEGE` | the besieger reduces an Elite to fight on | `extend` / `stop` |
| `ADVANCE` | the attacker advances into the emptied region | `advance` / `stay`, units if a choice |
| `RECRUIT` | which figure where, or end recruitment | `nation`, `unit`, `region`, or `end` |
| `MOVE_COMPANIONS` | which Companions move where, or end | `characters`, `from`, `to`, or `end` |
| `JOIN_GROUP` | a Companion joins which group | `character`, `group` |
| `SEPARATE_COMPANIONS` | which Companions leave the Fellowship, and where to | `characters`, `to` |
| `MOVE_MINIONS` | which Nazgûl or Minion flies where, or end | `characters` / `nazgul` count, `from`, `to`, or `end` |
| `CHOOSE_GUIDE` | the new Guide | `character` |
| `GUIDE_ABILITY` | use the Guide's ability (e.g. Gollum's reveal) | `use` / `skip` |
| `HUNT_CASUALTY` | Hunt damage: the Guide, a random Companion, or Corruption | `guide` / `random` / `corruption`, `ring` (use the Ring) |
| `REVEAL_FELLOWSHIP` | where the revealed Fellowship appears | `region` |
| `WHITE_RIDER` | Gandalf the White cancels the Nazgûl's Leadership | `use` / `skip` |
| `DISCARD_EXCESS_CARD` | which card to discard down to six | `card` |
| `CARD_CHOICE` | a card's own question (targets, amounts, yes/no) | `card` + the card's fields (`region`, `nation`, `character`, `count`, `yes`) |

A referee must not add kinds without a protocol version change; a bot must answer any kind it receives (option 0 is
always a legal fallback).

## 6. The vocabulary

Stable, lower-case keys from the rulebook's names; the full lists are in [`vocabulary/vocabulary-0.1.json`](vocabulary/vocabulary-0.1.json).

- **Sides**: `FREE_PEOPLES`, `SHADOW`.
- **Nations**: `DWARVES`, `ELVES`, `GONDOR`, `NORTH`, `ROHAN`, `ISENGARD`, `SAURON`, `SOUTHRONS_EASTERLINGS`.
- **Regions**: the 105 regions as slugs of their printed names: `minas-tirith`, `fords-of-isen`, `the-shire`,
  `barad-dur`, … The vocabulary file also gives each region's Nation, Settlement and neighbours (the referee's map,
  so differences show up before a game, not during it). On the Mordor Track the Fellowship's `mordor` is the step
  number, 0 to 5.
- **Units**: `regular`, `elite`, `leader`; `nazgul` (a Nazgûl figure, not the Witch-king).
- **Characters**: `gandalf-the-grey`, `strider`, `boromir`, `legolas`, `gimli`, `meriadoc`, `peregrin`, `gollum`,
  `gandalf-the-white`, `aragorn`, `witch-king`, `saruman`, `mouth-of-sauron`; the Ring-bearers are `ring-bearers`.
- **Cards**: one key per card from its side, deck and number in the printed card list: `fp-char-01` … `fp-char-24`,
  `fp-strat-01` … `fp-strat-24`, `sh-char-01` … `sh-char-24`, `sh-strat-01` … `sh-strat-24`; the vocabulary file gives
  each key's printed title. Card texts are not part of the protocol.
- **Action die faces**: `CHARACTER`, `ARMY`, `MUSTER`, `ARMY_MUSTER`, `EVENT`, `WILL_OF_THE_WEST`, `EYE`.
- **Hunt tiles**: by kind `eye`, `3`, `2`, `1`, `2r`, `1r`, `0r` (r = reveal); the special tiles by their own key
  (`elven-cloaks`, `elven-rope`, `phial-of-galadriel`, `smeagol-helps-nice-master`, `shelobs-lair`, `the-ring-is-mine`,
  `on-on-they-went`, `give-it-to-uss`).
- **Political steps**: 0 (at war) … 3; `active` true or false.

## 7. The view

Sent with every `decide` (and on request with `{"type":"get_view","id":…}`). It is **exactly what the deciding side may
know**: the public board, its own hand, and counts for what is hidden.

```
{"turn":4,"phase":"ACTION_RESOLUTION","to_act":"SHADOW",
 "regions":{"minas-tirith":{"control":"FREE_PEOPLES","units":[{"nation":"GONDOR","unit":"regular","n":3},
                                                              {"nation":"GONDOR","unit":"elite","n":1},
                                                              {"nation":"GONDOR","unit":"leader","n":1}],
                            "characters":[],"siege":false}, …},
 "politics":{"ROHAN":{"step":1,"active":true}, …},
 "fellowship":{"region":"rivendell","progress":2,"corruption":3,"hidden":true,"mordor":null,
               "guide":"gandalf-the-grey","companions":["gandalf-the-grey","legolas","gimli","meriadoc","peregrin"]},
 "characters":{"strider":{"where":"region","region":"bree"},"the-witch-king":{"where":"not_in_play"}, …},
 "dice":{"FREE_PEOPLES":[{"die":0,"face":"CHARACTER","used":false}, …],"SHADOW":[…]},
 "hunt":{"box":{"eyes":3,"FREE_PEOPLES":1},"pool":{"eye":4,"3":3,"2":2,"1":2,"2r":1,"1r":2,"0r":2},"drawn":[…]},
 "cards":{"hand":["sh-strat-07","sh-char-12"],"opponent_hand":3,
          "decks":{"FREE_PEOPLES":{"character":15,"strategy":17},"SHADOW":{"character":14,"strategy":16}},
          "discards":{"FREE_PEOPLES":["fp-char-03"],"SHADOW":[]},"on_table":["sh-strat-02"]},
 "victory_points":{"FREE_PEOPLES":0,"SHADOW":2},
 "elven_rings":{"FREE_PEOPLES":3,"SHADOW":0},
 "battle":null}
```

- The Fellowship's **true region** is never shown: its last known region and its progress are public, as on the board.
- A battle in progress is in `battle` (the regions, the Armies, the round, the Combat cards revealed so far, the dice
  rolled, the hits left to take).
- A referee may add fields; a bot ignores what it doesn't know.

## 8. Events (optional)

Bots that keep their own state can follow the game step by step:

```
{"type":"event","game":"g-…","seq":231,"event":{"kind":"dice_rolled","side":"SHADOW","faces":["EYE","ARMY",…]}}
{"type":"event","game":"g-…","seq":232,"event":{"kind":"choice","side":"FREE_PEOPLES","decision":"ACTION","option":{…}}}
{"type":"event","game":"g-…","seq":233,"event":{"kind":"card_drawn","side":"SHADOW","card":"sh-char-12"}}
```

- Each side receives only what it may see: the opponent's drawn card arrives as `{"kind":"card_drawn","side":"…",
  "deck":"character"}` without the card.
- Events are a convenience. The view in each `decide` is authoritative; a bot that disagrees with it resyncs from it.
- A bot announces in its `hello` whether it wants events (`"events":true`).

## 9. Rules and conformance

- **Which rules**: the Second Edition rulebook with the published FAQ and errata (dated; the referee names its version
  in `hello`). Where engines disagree, the referee's rules decide the game; disagreements found in matches are
  collected and settled in a shared list (our first two bridges found about twenty, e.g. map borders, the order of the
  Hunt's damage and reveal, some cards' requirements).
- **Referee conformance**: a set of recorded games (the seed's dice, draws and tiles plus every choice) that a referee
  must replay to the same positions and results. Each conforming referee can then run games for any pair of bots.
- **Bot conformance**: answers every kind of §5, only with listed options, within its clock.

## 10. Matches

A match runner (any referee) plays two bots on **paired seeds** (each seed twice, the sides swapped), records each game
(seed, both bots' names and versions, every choice, the result, and both bots' `info`), and reports the score per
side. Records use the same vocabulary, so any referee can replay and check them.

## 11. Open points for discussion

1. **Granularity**: are the kinds of §5 the right steps for everyone? Some engines play an Army move as one compound
   action; some ask a separation's destination differently. Atomic steps are the common ground, at
   the cost of more round trips (cheap locally).
2. **Shared randomness for fairness**: should the referee commit to the seed in advance (a hash in `new_game`,
   revealed in `game_over`), so both authors can verify the dice?
3. **Expansions** (Lords, Kings, Warriors of Middle-earth): later versions; `variant` and new kinds.
4. **Remote play between servers** (each author hosts their own bot): WebSocket with an authentication token.
5. **Human play**: the same protocol could let a person's client play through a referee; out of scope for 0.1.
6. **Who hosts the reference referee** and the conformance games.
