# WotR Bot Protocol (draft 0.2)

A text protocol that lets computer opponents for **War of the Ring, Second Edition** (the base game and, since 0.2,
the expansion **Lords of Middle-earth** with and without its Council of Rivendell) play each other, and people, whatever
language or rules engine each is written in. Draft for discussion with the authors of other War of the Ring bots
(0.1: 2026-10-21; 0.2: 2026-10-24); nothing here is final.

**Status (2026-10-24).** A referee implementing this draft runs as an open, hosted referee (§12; "Connecting your bot"
at the end), which also seats bots in games against people (§14). Where the implementation had to settle what the
draft left open, or differs from it, the text says **changed in implementation:** at that place. **0.2** adds the
rulesets and Lords of Middle-earth (§13) and is backwards compatible: a 0.1 bot keeps working unchanged and is only
ever given base games (CHANGELOG.md). The `game` clock is used in online play (§14); matches use `per_decision`, and
forfeiting on a timeout is a rule of the hosted referee's matches (§12).

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
- **Remote** (changed in implementation: the bot dials the referee): the bot opens a
  **WebSocket** to the referee, e.g. the hosted referee `wss://wotr.behindmedia.com/referee` (§12),
  one message per text frame; the referee speaks first (`hello`) once connected. The bot authenticates with a **token**,
  in the URL (`?token=…`), as a bearer token of the WebSocket's request, or as `"token"` in its `hello`; a bot without a known token gets
  `{"type":"error","id":1,"code":"unauthorized"}` and the connection closes. A plain TCP stream (one message per line)
  is the same protocol (not offered by the hosted referee yet).
- Every message has a `"type"`. Requests from the referee that need an answer carry an `"id"`; the answer repeats it.
- Unknown fields are ignored (forward compatibility). Unknown message types get an `error` answer if they carry an
  `id`, and are ignored otherwise.

## 3. The session

```
referee → bot   {"type":"hello","protocol":"wotr-bot/0.2","referee":"wotr-referee 2026.10","id":1}
bot → referee   {"type":"hello","id":1,"protocol":"wotr-bot/0.2","name":"ExampleBot","version":"1.0","author":"…",
                 "events":true,"rulesets":["base","lome","lome:council"],
                 "options":[{"name":"sims","type":"int","default":300,"min":1,"max":100000}]}
referee → bot   {"type":"options","values":{"sims":300}}
referee → bot   {"type":"new_game","id":2,"game":"g-87000005-fp-a","side":"SHADOW","rules":"base-2e","variant":[],
                 "seed_bot":12345,"clock":{"kind":"per_decision","ms":10000}}
bot → referee   {"type":"ready","id":2}
… decisions and events …
referee → bot   {"type":"game_over","game":"g-87000005-fp-a","winner":"FREE_PEOPLES","how":"RING_DESTROYED","turn":9}
referee → bot   {"type":"quit"}
```

- A referee may send a `match` object in `options`: the match's rules and the bot's seat (§12). A bot that does not
  use it ignores it.
- **One game at a time per connection** (0.1 and 0.2). A match runner opens one connection per bot per game, or
  reuses it (the reference referee reuses it for the whole match).
- `seed_bot` is the bot's own seed, for reproducible matches. The game's seed is **never** sent: it would reveal the
  dice and the decks.
- `rules`: `"base-2e"` is the Second Edition base game with the published errata (see §9). `variant` lists the
  expansion and its variants the game is played with (0.2, §13: `["lome"]`, `["lome","council"]`; then also
  `ruleset`, its canonical key); empty for the base game.
- The bot's `hello` (changed in implementation, all optional): `events` (true: send the events of §8), `token` (§2),
  `rulesets` (0.2, §13: the rules it plays; absent: the base game only),
  `extensions` (names of referee-specific additions it wants), `options` (each with
  `name`, `type` `int`/`bool`/`string`, `default`, `min`, `max`; the referee answers every declared option in
  `options.values`, its default unless the match sets it).
- `game_over`: `winner` is null for a draw at the referee's turn cap; `how` is the rulebook's victory
  (`RING_DESTROYED`, `CORRUPTION`, `SHADOW_MILITARY`, `FREE_PEOPLES_MILITARY`), `TURN_CAP`, `FORFEIT` or `ABORTED`
  (the referee ended the game from outside: a match's time limit, a cancelled match, a restart; `winner` is null and
  the game does not count).

## 4. Decisions

```
referee → bot   {"type":"decide","id":17,"game":"g-87000005-fp-a","decision":{
                   "kind":"ACTION","side":"SHADOW","prompt":"Choose an Action die and what to do with it, or pass",
                   "options":[
                     {"o":0,"kind":"use_die","die":2,"face":"ARMY","action":"move_armies","text":"Die 3 (Army): move Armies"},
                     {"o":1,"kind":"use_die","die":2,"face":"ARMY","action":"attack","text":"…"},
                     {"o":2,"kind":"use_die","die":4,"face":"EVENT","action":"play_card","card":"sh-strat-07","as":"EVENT","text":"…"},
                     {"o":3,"kind":"pass","text":"Pass"}],
                   "fingerprint":"3f9a5c0e7d21b8a4"},
                 "view":{…},
                 "clock":{"left_ms":10000}}
bot → referee   {"type":"choice","id":17,"o":1,"fingerprint":"3f9a5c0e7d21b8a4","info":{"visits":2400,"value":0.61}}
```

- **One decision = one question with a closed list of options.** The bot answers with the option's `o`. Options are
  described in the shared vocabulary (§6), so a bot can understand them, but it never has to construct one. Each
  option also carries `text`, the referee's words for it (for logs and people; not part of the option's identity).
  The decision may carry a `context` (changed in implementation: what the question is about, e.g. the battle's
  `region`, `round` and `hits` for a casualty, the `card` and `question` of a card's question, `from`/`to`/`nation`/
  `unit`/`available` for an Army split).
- **`fingerprint`** (changed in implementation: defined): 64-bit FNV-1a over the UTF-8 text
  `SIDE\nKIND\nN\n` followed by each option's compact JSON as sent, without its `text` field, each followed by `\n`;
  16 lower-case hex digits (FNV-1a 64: start from `0xcbf29ce484222325`, for each byte xor it in, then multiply by
  `0x100000001b3` modulo 2⁶⁴). The bot echoes it so the referee can detect an answer to a stale question; a bot may
  leave it out.
- **Atomic steps.** Compound actions are asked step by step, in the rulebook's order, e.g. an Army move is: the die and
  the action (`ACTION`), then which Army from where to where (`ARMY_MOVE`), then which units go if not all
  (`ARMY_SELECTION`), then the next Army or the end (`ARMY_MOVE` again). This is the one place bots must meet the
  referee's granularity, so the kinds are fixed by this specification (§5), not by an engine.
- **`info`** (optional): anything the bot wants logged (visits, value, principal line). The referee records it and
  never shows it to the opponent.
- **Time**: `clock` says how much time is left for this decision (`per_decision`) or for the whole game (`game`, with
  an increment; used in online play, §14). A bot that misses the deadline gets a `timeout` notice
  (`{"type":"timeout","id":17,"game":"…","played":0}`); the referee then plays option 0 (or, if the match's rules say so,
  the N-th timeout in a game forfeits it). An answer that comes later is ignored.
- **Illegal or unknown answers**: the referee answers `{"type":"error","id":17,"code":"illegal_option"}` and asks again,
  once (a new `decide` with a new id); a second illegal answer forfeits the game. Codes (changed in implementation):
  `illegal_option` (no such `o`), `stale_fingerprint` (an echoed fingerprint that is not the decision's),
  `not_a_choice` (another message answered the `decide`), `unknown_type`, `unauthorized`; a hosted referee also
  `unavailable`, `rate_limited`, `busy`, `seat_taken`, `match_over`, `line_too_long` (§12). A bot whose connection
  ends forfeits the game at its next decision.
- **`get_view`**: while a decision is open, `{"type":"get_view","id":…}` is answered with
  `{"type":"view","id":…,"view":{…}}`.

## 5. Decision kinds (0.1)

Every option has a `kind` (what it does) and the fields listed. All 26 kinds are implemented; the fields are as built
(changed in implementation where the draft named them otherwise, marked ✱ and explained under the table). 0.2 adds
five kinds and some options for Lords of Middle-earth (§13); a base game asks only these 26.

| Kind | The question | Options (`kind` and fields) |
|---|---|---|
| `FELLOWSHIP_PHASE` | declare the Fellowship, enter Mordor, change the Guide, or done | `declare` + `region`; `enter_mordor`; `guide` + `character`; `done` |
| `HUNT_ALLOCATION` | how many dice into the Hunt Box (Shadow) | `hunt_dice` + `count` |
| `ACTION` | which die, and which action with it (or pass, or skip a die) | `use_die` + `die`, `face`, `action` and the action's fields ✱; `skip_die` + `die`, `face`; `elven_ring` + `die`, `from`, `to` ✱; `pass` |
| `ARMY_MOVE` | which Army moves where, or end the move | `army_move` + `from`, `to`, `all` (false: the units are chosen next); `end` |
| `ARMY_SELECTION` | how many of each unit kind move | `count` + `count`, `nation`, `unit` (or `character` for a Character going along: 0 or 1) |
| `CHOOSE_ATTACK` | which attack (from where, which region) | `attack` + `from`, `to`, `all` ✱ |
| `FIELD_OR_SIEGE` | the defender of a Stronghold: field battle or withdraw | `field`; `siege` |
| `COMBAT_CARD` | a Combat card for this round, or none | `combat_card` + `card`; `none` |
| `CASUALTY` | which unit to remove or reduce for a hit | `casualty` + `nation`, `unit` (`regular`/`elite`), `effect` (`remove` / `reduce`) |
| `REMOVE_EXCESS_UNIT` | which unit leaves an overfull region or siege | `remove_unit` + `nation`, `unit`, `region` |
| `CEASE_ATTACK` | the attacker continues or ceases | `continue`; `cease` |
| `RETREAT` | the defender retreats where, or stands | `retreat` + `region`; `stand` |
| `EXTEND_SIEGE` | the besieger reduces an Elite to fight on | `extend` + `nation`; `stop` |
| `ADVANCE` | the attacker advances into the emptied region | `advance` + `all` (false: the units are chosen next, as `ARMY_SELECTION`); `stay` |
| `RECRUIT` | which figure where, or end recruitment | `recruit` + `region`, `nation`, `unit`; `end` |
| `MOVE_COMPANIONS` | which Companion moves where, or end | `move_companion` + `character`, `from`, `to` ✱; `end` |
| `JOIN_GROUP` | a Companion joins the group moving | `join` / `stay` + `character`, `to` ✱ |
| `SEPARATE_COMPANIONS` | which Companions leave the Fellowship, and where to | `separate` + `character`; `separate_to` + `to` ✱ |
| `MOVE_MINIONS` | which Nazgûl or Minion flies where, or end | `select_nazgul` + `from`; `select_minion` + `character`, `from`; `move_nazgul` + `from`, `to`; `move_minion` + `character`, `from`, `to`; `end` ✱ |
| `CHOOSE_GUIDE` | the new Guide | `guide` + `character` |
| `GUIDE_ABILITY` | use the Guide's ability (e.g. Gollum's reveal) | `use`; `skip` |
| `HUNT_CASUALTY` | Hunt damage: the Guide, a random Companion, or Corruption | `guide`; `random`; `corruption` (use the Ring) |
| `REVEAL_FELLOWSHIP` | where the revealed Fellowship appears | `reveal` + `region` (and `through_moria`: true where "Balrog of Moria" makes the path matter) |
| `WHITE_RIDER` | Gandalf the White cancels the Nazgûl's Leadership | `use`; `skip` |
| `DISCARD_EXCESS_CARD` | which card to discard down to six | `discard` + `card` |
| `CARD_CHOICE` | a card's own question (targets, amounts, yes/no) | `card_choice` + `card`, `answer` and a typed field ✱; `draw` + `deck` (a bonus draw) ✱ |

✱ Changed in implementation:

- **`ACTION`'s actions** (`use_die`'s `action`): `draw_card` + `deck`; `move_armies`; `move_army_with_leader`
  (a Character result moving one Army with a Leader); `attack`; `attack_with_leader`; `recruit`; `diplomacy` +
  `nation`; `move_companions`; `separate_companions`; `move_minions`; `move_fellowship`; `hide_fellowship`;
  `hide_fellowship_strider` (any result, Strider as Guide); `play_companion` / `play_minion` + `character`, `region`;
  `companion_politics` + `character` (Boromir, Legolas, Gimli); `voice_of_saruman` + `upgrade`; `play_card` + `card`,
  `as` (the die result it is played with); `force_discard` + `card` (the opponent's table card), `any_die`,
  `elven_ring` (true: giving up an Elven Ring as well), `pay` (cards discarded from the hand as the price). The
  draft's `character`, `nation`, `region` are these actions' fields. An Elven Ring is its own option: `elven_ring` +
  `die`, `from`, `to` (the die's new face; the same player then acts).
- **`CHOOSE_ATTACK`**: `all` (false: a rearguard is chosen next) instead of `with_leader`, which is the `ACTION`'s
  choice (`attack` or `attack_with_leader`).
- **`MOVE_COMPANIONS`, `JOIN_GROUP`**: one Companion per option; the others in his region are then asked one by one
  whether they join his group (`join` / `stay`, with the Companion asked and the destination), instead of a list of
  `characters` and a `group`.
- **`SEPARATE_COMPANIONS`**: the Companions leaving are picked one by one (`separate`), then the destination
  (`separate_to`), instead of `characters` and `to` at once.
- **`MOVE_MINIONS`**: a Nazgûl is picked by its region (`select_nazgul`), a Minion by name (`select_minion`), then the
  destination (`move_nazgul`, `move_minion`), instead of a `nazgul` count.
- **`CARD_CHOICE`**: `card` is the card asking; `answer` is the referee's word for the answer (cards in it as keys of
  §6, e.g. `minas-tirith>osgiliath`, `minas-tirith:REGULAR`, `hand`, `move`); where the answer is one thing, its
  typed field as well: `yes` (true/false), `skip` (true), `region`, `character`, `nation`, `count`, `deck`,
  `target_card` (a card named by the answer), `from` + `to` (an Army's move), `region` + `unit` (a figure). A bonus draw
  (Gandalf the Grey as Guide, the Palantír of Orthanc) is `CARD_CHOICE` with `draw` + `deck` options and a context
  `{"deck": …}` (or none for either deck).

A referee must not add kinds without a protocol version change (0.2 is one: §13); a bot must answer any kind it
receives (option 0 is always a legal fallback).

## 6. The vocabulary

Stable, lower-case keys from the rulebook's names; the full lists are in [`vocabulary/vocabulary-0.2.json`](vocabulary/vocabulary-0.2.json)
(a superset of [`vocabulary-0.1.json`](vocabulary/vocabulary-0.1.json), the base game's, which stays as it was; what
Lords of Middle-earth adds is marked `"expansion": "lome"` there and listed in §13).

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
  each key's printed title. Card texts are not part of the protocol. Decks: `character`, `strategy`. An expansion's
  cards have the expansion's key first (`lome-fp-char-25`, §13).
- **Action die faces**: `CHARACTER`, `ARMY`, `MUSTER`, `ARMY_MUSTER`, `EVENT`, `WILL_OF_THE_WEST`, `EYE`.
- **Hunt tiles** (changed in implementation: by tile, as in the vocabulary file): `eye-1` … `eye-4`, `3-1` … `3-3`,
  `2-1`, `2-2`, `1-1`, `1-2`, `2r`, `1r-1`, `1r-2`, `0r-1`, `0r-2` (r = reveal); the special tiles by their own key
  (`elven-cloaks`, `elven-rope`, `phial-of-galadriel`, `smeagol-helps-nice-master`, `shelobs-lair`, `the-ring-is-mine`,
  `on-on-they-went`, `give-it-to-uss`).
- **Political steps**: 0 (at war) … 3; `active` true or false.

## 7. The view

Sent with every `decide` (and on request with `{"type":"get_view","id":…}`). It is **exactly what the deciding side may
know**: the public board, its own hand, and counts for what is hidden. As built (excerpt):

```
{"viewer":"FREE_PEOPLES","turn":1,"phase":"ACTION_RESOLUTION","to_act":"FREE_PEOPLES","active_side":"FREE_PEOPLES",
 "regions":{"grey-havens":{"control":"FREE_PEOPLES","units":[{"nation":"ELVES","unit":"regular","n":1},
                                                             {"nation":"ELVES","unit":"elite","n":1},
                                                             {"nation":"ELVES","unit":"leader","n":1}],
                           "characters":[],"siege":false}, …},
 "politics":{"ROHAN":{"step":2,"active":false}, …},
 "reinforcements":{"GONDOR":{"regular":6,"elite":4,"leader":3,"nazgul":0}, …},"casualties":{…},
 "fellowship":{"region":"rivendell","progress":0,"corruption":0,"hidden":true,"mordor":null,
               "guide":"gandalf-the-grey","companions":["gandalf-the-grey","strider","boromir","legolas","gimli","meriadoc","peregrin"]},
 "characters":{"strider":{"where":"fellowship"},"witch-king":{"where":"not_in_play"}, …},
 "dice":{"FREE_PEOPLES":[{"die":0,"face":"MUSTER","status":"available","used":false}, …],"SHADOW":[…]},
 "hunt":{"box":{"FREE_PEOPLES":0,"SHADOW":2},"pool":["eye-1","eye-2",…],"reserve":["elven-cloaks",…],"ready":[],
         "drawn":[],"removed":[],"shadow_must_hunt":false},
 "cards":{"hand":["fp-char-14","fp-strat-06"],"discarded_face_down":[],"opponent_hand":2,
          "opponent_hand_by_deck":{"character":1,"strategy":1},"opponent_discarded_face_down":0,
          "decks":{"FREE_PEOPLES":{"character":23,"strategy":23},"SHADOW":{"character":23,"strategy":23}},
          "discards":{"FREE_PEOPLES":[],"SHADOW":[]},"on_table":{"FREE_PEOPLES":[],"SHADOW":[]}},
 "victory_points":{"FREE_PEOPLES":0,"SHADOW":0},
 "elven_rings":{"FREE_PEOPLES":3,"SHADOW":0},"elven_ring_used":{"FREE_PEOPLES":false,"SHADOW":false},
 "battle":null,"result":null}
```

- The Fellowship's **true region** is never shown: its last known region and its progress are public, as on the board.
- A battle in progress is in `battle`: `attacker`, `battle` (`field`, `siege`, `sortie`), `from`, `region`, `round`,
  `attackers` (the units that attack), `event_card` (a card that started it), `cards_revealed`, the Combat cards
  revealed so far (`attacker_card`, `defender_card`; a hidden one only as `attacker_card_back`, its deck), `step`, and
  the hits left to take (`hits_on_attacker`, `hits_on_defender`).
- Changed in implementation: the Hunt pool and the other places of the tiles (`reserve`: special tiles not yet played,
  `ready`: played, entering the pool on the Mordor Track, `drawn`, `removed`) are lists of tile keys (§6); a die has a
  `status` (`unrolled`, `available`, `used`, `hunt_box`) besides `used`; the view names its `viewer`, the `active_side`
  and the `result`; reinforcements and casualties per Nation; the opponent's hand and face-down discards as counts
  (also per deck: the backs are public).
- A referee may add fields; a bot ignores what it doesn't know.
- A referee writes the view only from what the side may know, never from the full state: two positions that differ
  only in what the side cannot see (the opponent's cards dealt anew, a hidden Combat card) give the same view, and no
  unseen card's key appears in it.

## 8. Events (optional)

Bots that keep their own state can follow the game step by step:

```
{"type":"event","game":"g-…","seq":231,"event":{"kind":"choice","side":"FREE_PEOPLES","decision":"ACTION","o":3,"option":{…}}}
{"type":"event","game":"g-…","seq":232,"event":{"kind":"random_action_dice","side":"SHADOW","faces":["EYE","ARMY",…]}}
{"type":"event","game":"g-…","seq":233,"event":{"kind":"random_card_draw","side":"SHADOW","deck":"character","card":"sh-char-12"}}
{"type":"event","game":"g-…","seq":234,"event":{"kind":"card_drawn","side":"SHADOW","deck":"character","card":"sh-char-12"}}
```

- Each side receives only what it may see: the opponent's drawn card arrives without the card (`{"kind":
  "random_card_draw","side":"…","deck":"character"}`).
- Events are a convenience. The view in each `decide` is authoritative; a bot that disagrees with it resyncs from it.
- A bot announces in its `hello` whether it wants events (`"events":true`).
- Changed in implementation, the events as built, in the order they happen (the setup's random outcomes come first,
  before its board events), numbered by `seq` per game and side:
  - **`choice`**: every decision answered, by either side: `side`, `decision` (the kind), `o` and `option` (its fields,
    without `text`). Two choices are secret from the opponent and show only their back: the attacker's Combat card
    (`{"kind":"combat_card","hidden":true,"deck":"strategy"}`; the card shows with `combat_cards_revealed`) and a card
    discarded face down (`{"kind":"discard","hidden":true,"deck":…}`). An option of 0.1 never needs more (0.2 adds a
    third, a Companion's secret version, §13).
  - **`random_*`**: every random outcome, in the order the referee drew it, so that a bot with an engine of its own
    can replay the game with the referee's dice: `random_action_dice` (`side`, `faces`), `random_card_draw` (`side`,
    `deck`, and `card` for its own side), `random_hunt_tile` (`tile`), `random_roll` (`side` if any, `roll`: `combat`,
    `leader_reroll`, `hunt`, `hunt_reroll`, `combat_card`, `card`, `tile`, `other`; `dice`: the d6 values),
    `random_companion` (`character`: a Companion drawn at random), `random_hand_card` (`side`, `card`: a card discarded
    at random from the hand, face up).
  - **Board events**, for logs and checks: `turn_started`, `phase_started`, `dice_recovered`, `hunt_dice_allocated`,
    `action_dice_rolled`, `die_used` (with the `action` as in §5), `die_skipped`, `passed`, `elven_ring_used`,
    `card_drawn`, `card_discarded` (`face_down`; the card only where it may be seen), `card_played`,
    `table_card_discarded`, `army_moved` (`pieces`: `nation`, `unit`, `count`), `settlement_captured`,
    `settlement_recaptured`, `figure_recruited`, `unit_removed`, `nation_activated`, `politics_advanced`,
    `battle_started` (`battle`), `combat_card_chosen` (`deck`, the back), `combat_cards_revealed`, `combat_rolled`,
    `casualty_taken`, `figure_eliminated`, `attack_ceased`, `army_retreated`, `retreated_into_siege`, `siege_started`,
    `siege_ended`, `battle_ended`, `character_moved`, `companions_separated`, `character_entered_play`,
    `character_replaced`, `character_eliminated`, `companion_lost_to_hunt` (`loss`), `guide_changed`, `nazgul_moved`,
    `fellowship_moved`, `hunt_rolled`, `hunt_tile_drawn`, `hunt_tile_revealed`, `corruption_changed`,
    `fellowship_declared`, `fellowship_revealed`, `fellowship_hidden`, `fellowship_displaced`,
    `fellowship_entered_mordor`, `card_dice_rolled`, `game_over`. Their fields are snake_case, cards as keys of §6.

## 9. Rules and conformance

- **Which rules**: the Second Edition rulebook with the published FAQ and errata (dated; the referee names its version
  in `hello`). Where engines disagree, the referee's rules decide the game; disagreements found in matches are
  collected and settled in a shared list (bridging three bots found about twenty, e.g. map borders, the order of the
  Hunt's damage and reveal, some cards' requirements).
- **Referee conformance**: a set of recorded games (the seed's dice, draws and tiles plus every choice) that a referee
  must replay to the same positions and results. Each conforming referee can then run games for any pair of bots.
  Changed in implementation, the format ([`conformance/game-*.json`](conformance/), three base games of a searching bot
  at a low budget, won by the Free Peoples (Ring), by the Shadow (Corruption) and by the Shadow (military); since 0.2
  also four games of Lords of Middle-earth, §13):
  `seed`, `bots`, `setup` (the random outcomes before the first decision, as `random_*` events seen by the side that
  drew them), `steps` (per decision: `side`, `decision`, `fingerprint`, the `o` chosen, and the step's `random`
  outcomes), `result` (`winner`, `how`, `turn`) and `final_views` (both sides' views at the end). A referee replays the
  outcomes (not the seed) and must reach every recorded decision with the same fingerprint, the same result and the
  same final views.
- **Bot conformance**: answers every kind of §5 (and, for a bot that declares an expansion, of §13), only with listed
  options, within its clock.

## 10. Matches

A match runner (any referee) plays two bots on **paired seeds** (each seed twice, the sides swapped), records each game
(seed, both bots' names and versions, every choice, the result, and both bots' `info`), and reports the score per
side. Records use the same vocabulary, so any referee can replay and check them.

## 11. Open points for discussion

1. **Granularity**: are the kinds of §5 the right steps for everyone? Some engines play an Army move as one compound
   action; some ask a separation's destination differently. Atomic steps are the common ground, at
   the cost of more round trips (cheap locally; about 1 ms a decision through the reference referee).
2. **Shared randomness for fairness**: should the referee commit to the seed in advance (a hash in `new_game`,
   revealed in `game_over`), so both authors can verify the dice?
3. **Expansions** (Lords, Kings, Warriors of Middle-earth): Lords of Middle-earth and its Council of Rivendell are in
   0.2 (§13); Kings and Warriors of Middle-earth later, the same way (a ruleset key, `variant`, new kinds).
4. **Remote play between servers** (each author hosts their own bot): settled for 0.1 as the bot dialling the
   referee's WebSocket with a token (§2).
5. **Human play**: the same protocol could let a person's client play through a referee; out of scope for 0.1 and 0.2
   (bots play people through the hosted site instead, §14).
6. **Who hosts the reference referee** and the conformance games: the reference referee is hosted at
   `wss://wotr.behindmedia.com/referee` (§12); matches are made by members of the site. The specification, the vocabulary, the conformance games and the example clients go to a public
   repository of their own.
7. **Skipped questions** (found in implementation): the reference referee does not ask for a Combat card when the side has none
   it can play, so whether a side was asked tells its opponent a little about its hand. The reference referee keeps that
   behaviour; a bot following the game sees it as a `choice` event that is not there. Should
   a referee always ask (with `none` as the only option)?

## 12. A hosted referee

A referee open to the public plays **matches** made in advance, each with fixed rules and two seat tokens.

- **Seats**: a token is valid for one seat of one match; one connection per seat at a time. Both seats connected,
  the games begin. A seat that drops forfeits the game in progress; it may reconnect with its token within 5
  minutes for the next game, else it forfeits the remaining games.
- **The `match` object** in `options`:
  `{"id":"m-…","name":"nightly","games":2,"max_turns":25,"clock_ms":10000,"timeouts_forfeit":3,"paired_seeds":false,"seat":"A","opponent":"bot","games_done":0}`.
  `max_turns` null: no turn cap. `timeouts_forfeit` 0: a timeout plays option 0; N: the N-th timeout in a game
  forfeits it. `paired_seeds` true: one seed for each pair of games, the sides swapped (a bot that remembers game 1
  knows the other side's opening hand in game 2). `opponent`: `bot`, or `greedy` (the referee's own test bot).
  `games_done`: games of the match already played (after a reconnection).
- **Sides**: a coin flip for game 1's Free Peoples, then alternating.
- **Ids and seeds**: game ids are random; `seed_bot` is derived from a secret of the referee and the game id, never
  from the game's seed.
- **Extensions**: none.
- **Limits**: a message of at most 16 KiB; at most 8 `get_view` per decision (more: `error` `rate_limited`, the
  decision stays open); at most 20 messages a second that answer nothing asked (more: `rate_limited`, and the
  connection closes); a bot's name and version are kept to 64 characters.
- **Refusals**, each `{"type":"error","code":…,"message":…}` followed by the end of the connection: `unavailable`
  (the referee is off or restarting), `unauthorized` (unknown token), `rate_limited` (too many wrong tokens from one
  address), `busy` (too many matches running: try later), `seat_taken` (that seat is connected), `match_over` (the
  match is finished, cancelled or expired), `line_too_long`.
- **Time limits**: a match not started within 24 hours expires; one running longer than 12 hours ends, its game in
  progress not counted (`ABORTED`).
- **Rules**: a match between two bots plays the base game; games of Lords of Middle-earth are played against people
  (§14), with bots that declare it (§13).

## 13. Rulesets and Lords of Middle-earth (0.2)

0.2 adds the expansion **Lords of Middle-earth** (Ares Games) for War of the Ring, Second Edition, with and without
its **Council of Rivendell** variant. Everything of 0.1 is unchanged for the base game, byte for byte: a 0.1 bot keeps
working and is only ever given base games. The expansion's rules are its rulebook's (with the published FAQ, as for the
base game, §9); this section names only what a bot must read and answer.

- **Version**: a 0.2 referee says `"protocol":"wotr-bot/0.2"` in its `hello` and accepts any `wotr-bot/0.x` bot.
- **The bot declares its rules**: `"rulesets": ["base", "lome", "lome:council"]` in its `hello`. Keys: `base` (the
  base game), `lome` (Lords of Middle-earth), `lome:council` (Lords of Middle-earth with the Council of Rivendell);
  unknown keys are ignored. Absent, or none known: `["base"]`. A referee sends a bot only games of a ruleset it
  declared; the hosted site offers a bot to people's games by it (§14). A bot that only chooses among the listed
  options can declare every ruleset (the example bot declares none, so it plays the base game: add `"rulesets"` to its
  `hello`); a bot with an engine of its own declares what its engine knows.
- **`new_game`** of an expansion's game: `"rules": "base-2e"` as always, `"variant": ["lome"]` or
  `["lome", "council"]`, and `"ruleset": "lome"` or `"lome:council"` (the canonical key). A base game's `new_game` is as
  in 0.1 (`variant` empty, no `ruleset`).
- **The vocabulary's additions** ([`vocabulary-0.2.json`](vocabulary/vocabulary-0.2.json), each marked
  `"expansion": "lome"`, keys and short names only):
  - **Cards**, keyed with the expansion first: `lome-fp-char-25` … `lome-fp-char-28`, `lome-fp-strat-25`,
    `lome-fp-strat-26`, `lome-sh-char-25` … `lome-sh-char-28`, `lome-sh-strat-25`, `lome-sh-strat-26`;
    `lome-sh-char-17` ("A Balrog is Come!") takes the place of `sh-char-17` ("Balrog of Moria") in the deck;
    `lome-sh-char-00` ("We Shall Get It") is out of the decks until a rule brings it in. Cards out of the game are
    listed in the view (`lome.out_of_game`).
  - **Characters**: `elrond`, `galadriel`, `smeagol`, `balrog`, `gothmog`; the **versions** of a base character
    (`version_of` in the file): `gandalf-the-grey-narya` (Gandalf the Grey, Keeper of Narya),
    `mouth-of-sauron-black-numenorean`, `witch-king-chief`, and with the Council `strider-dunadan`,
    `boromir-captain-general`, `legolas-elven-prince`, `gimli-dwarven-lord`, `meriadoc-hobbit-of-the-shire`,
    `peregrin-hobbit-of-the-shire`.
  - **Special dice** (field `special_die`): `vilya`, `nenya`, `narya` (Free Peoples), `balrog`, `gothmog` (Shadow),
    each with its owner and its six faces in order (`remove` marks a face with the Remove star). The faces they add:
    `CARD_DRAW`, `USE_BALROG`.
  - **Elven Rings** (field `ring`): `vilya`, `nenya`, `narya`.
  - **Hunt tiles**: `smeagol-1` … `smeagol-4`.
  - **The Council's Action tokens** (field `token`): `move`, `advance`.
  - **Abilities** that ask as a card does: `he-sees-he-knows` (the Witch-king, Chief of the Ringwraiths).
- **Decision kinds** added (after the 26 of §5; in an expansion's game only):

| Kind | The question | Options (`kind` and fields) |
|---|---|---|
| `SPECIAL_DIE` | keep one of the special dice just rolled | `keep_special_die` + `special_die`, `face` |
| `KEEPER_RING` | use a Keeper's Ring now, or not (Vilya after an action, Nenya on an Eye tile) | `keeper_ring` + `ring`, `use` (true/false) |
| `SETUP_VERSION` | before the game, in secret: which version of a Companion plays (Gandalf the Grey or the Keeper of Narya; with the Council each Companion's) | `version` + `character` |
| `SETUP_GUIDE` | the initial Guide | `starting_guide` + `character` |
| `COUNCIL` | the Council of Rivendell: a Companion starting outside the Fellowship, or the end of that; an Action token; where a Companion who disappeared reappears | `start_outside` + `character`, `region`; `end`; `take_token` + `token`; `disappear_to` + `character`, `region` |

- **Options** added to the base kinds:
  - `ACTION`: `use_token` + `token` and the die action's fields (a Council Action token used as a die).
  - `EXTEND_SIEGE`: `evil_knowledge`.
  - `use_die` / `skip_die` of the kept special die carry `special_die` (its key; its `die` index comes after the
    standard dice).
  - `elven_ring` and the `force_discard` action carry `ring` (which Ring).
  - Die actions (`use_die`'s `action`): `use_narya` + `nation`; `play_keeper` + `character`, `region`;
    `activate_balrog`; `move_balrog` + `region`; `move_army_with_balrog`; `attack_with_balrog`; `deactivate_balrog`
    + `by_gandalf`; `gothmog_recruit` + `upgrade`; `great_sorcery` + `attack`; `guide_force_discard` + `card`.
    Minions enter play with their own keys (`play_minion` + `character`, e.g. `witch-king-chief`).
  - `CARD_CHOICE` (and its `context`) of an ability that asks as a card does has `ability` (its key) in place of
    `card`.
- **Secret choices**: `SETUP_VERSION` is secret like a face-down card. The opponent's `choice` event shows only
  `{"kind":"version","hidden":true,"character":BASE}` (which Companion, never which version), and its view shows the
  base character's key wherever that Companion is (the Guide included), listed in `lome.hidden_versions`. The version
  is revealed as the game shows it (when it becomes the Guide, leaves the Fellowship, or a card reveals it): a
  `version_revealed` event, and the true key from then on (listed in `lome.revealed_versions`).
- **Events** added: `random_special_die` (`special_die`, `face_index` 0–5 in the order of the die's faces in the
  vocabulary file, `face`, and `remove` when that face has the Remove star) among the random outcomes, after the
  standard dice of the same roll; board events in the same snake_case form, e.g. `special_die_rolled`,
  `special_die_kept`, `version_revealed`, `started_outside`, `action_token_taken`.
- **The view** gains, in an expansion's game only, `"lome"`: `ruleset`; `special_dice` (each `special_die`, `side`,
  `owner`, `status` (`not_in_pool`, `unrolled`, `rolled`, `available`, `set_aside`, `used`, `hunt_box`, `removed`),
  `face`, and `remove` on a rolled Remove star); `kept_special_die` per side; `elven_ring_owners` per Ring
  (`FREE_PEOPLES`, `SHADOW`, `OUT_OF_GAME`); `balrog_active`; `nenya_offered` and `we_shall_get_it_offered` (a tile,
  while it is offered); `revealed_versions` and `hidden_versions`; `out_of_game`, the cards out of the game per side;
  and with the Council `council` (`action_tokens`: `move` and `advance`, each `held` and `used`;
  `token_used_this_turn`; `fellowship_box_die`; `disappeared`). Example (the end of a Council game):

```
"lome":{"ruleset":"lome:council",
        "special_dice":[{"special_die":"vilya","side":"FREE_PEOPLES","owner":"elrond","status":"removed","face":null},
                        {"special_die":"narya","side":"FREE_PEOPLES","owner":"gandalf-the-grey-narya","status":"not_in_pool","face":null}, …],
        "kept_special_die":{"FREE_PEOPLES":null,"SHADOW":null},
        "elven_ring_owners":{"vilya":"OUT_OF_GAME","nenya":"SHADOW","narya":"OUT_OF_GAME"},"balrog_active":false,
        "revealed_versions":["gandalf-the-grey","boromir",…],"hidden_versions":[],
        "out_of_game":{"FREE_PEOPLES":[],"SHADOW":["sh-char-17","lome-sh-char-00"]},
        "council":{"action_tokens":{"move":{"held":false,"used":false},"advance":{"held":false,"used":false}},
                   "token_used_this_turn":false,"fellowship_box_die":null,"disappeared":{}}}
```

- **Conformance**: an expansion's conformance game has `variant` and `ruleset` at its top and replays as the base
  game's do (§9): [`conformance/game-201.json`](conformance/game-201.json) and
  [`game-202.json`](conformance/game-202.json) are Lords of Middle-earth (won by the Free Peoples (Ring) and by the
  Shadow (Corruption)), [`game-301.json`](conformance/game-301.json) and [`game-302.json`](conformance/game-302.json)
  Lords of Middle-earth with the Council of Rivendell (won by the Shadow (Corruption) and by the Free Peoples (Ring)).
  The three base games are unchanged.
- **What a bot that declares `lome` must handle**: the five kinds above (option 0 is always legal), the new options'
  fields where it reads them, the `lome` part of the view, and, if it follows the events, `random_special_die` and a
  hidden `version` choice. A bot that keeps its own copy of the game stands in for an opponent's hidden version with
  the base character until the game names it.

## 14. Online play

The hosted referee also seats bots in games against people on the site (wotr.behindmedia.com; README, "Play people on
the site"). The protocol is the same, with these additions; a bot that ignores them still plays, as long as it answers
within its game's time.

- **Connection**: a bot key (`wotr_bot_…`) instead of a seat token. One game at a time per connection; between games
  the connection waits, and the next `new_game` may come at any time. No `quit`.
- **The rules it plays** (0.2, §13): `rulesets` in the bot's `hello`, absent meaning the base game. People's
  challenges and quick match give a bot only games of the rules it declared.
- **`seek`** (optional, in the bot's `hello`): which games it takes.
  `{"real_time": {"min_base_s": 300, "max_base_s": 7200, "max_increment_s": 60}, "correspondence": {"max_days": 7}}`;
  `"real_time": false` for none; without `correspondence`, none. Default: real time from 5 minutes to 2 hours, an
  increment up to 60 seconds, no correspondence. Rated and side are not the bot's to choose: games against bots are
  never rated, and a bot plays either side.
- **The game clock** (§4's `game` clock): `new_game`'s `clock` is
  `{"kind": "game", "ms": 900000, "increment_ms": 10000}` or `{"kind": "correspondence", "days_per_move": 3}`; each
  `decide`'s `clock` is `{"left_ms": …, "opponent_ms": …, "increment_ms": …}` (your time left in the whole game) or
  `{"deadline": <ms since 1970>, "left_ms": …}`. A side earns the increment each time the decision passes to the other
  side. There is no time per decision and no `timeout` notice: a bot out of time loses the game. Read `kind` before
  `left_ms`.
- **Game ids** are the site's (letters, digits, `-`, `_`); `seed_bot` is never derived from the game's seed.
- **Coming back**: in a real-time game a bot whose connection drops has 2 minutes to connect again (its clock runs);
  its next connection gets `new_game` for the same game, every event of its side from the start (`seq` from 1 again),
  and the decision waiting. Later than that, it loses the game. In correspondence the game waits.
- **`game_over`**: `how` is a victory, `FORFEIT` with `detail` (`resigned` or `time`; `winner` says who), or `ABORTED`
  (no winner: the game ended before both sides moved, or the site took it away).
- **What it sees**: its side's view and events only. No chat reaches the bot, and the bot sends none: its greeting is
  set on its page and sent once when a game starts.
- **Limits** as the hosted referee's (§12); an illegal answer is asked once more; two illegal answers to one decision,
  or a broken limit, resign the game.
- **Refusals**: `unavailable`, `unauthorized` (also "waits for the admin's approval", "was suspended"), `rate_limited`,
  `busy` (as many connections as the bot may have).

## Connecting your bot

1. Start from [`examples/python/random_bot.py`](examples/python/random_bot.py) (standard library only): it answers
   `hello`, answers `new_game` with `ready`, and answers each `decide` with a random option. Replace the choice with
   your bot's.
2. Run it against a referee locally over stdin/stdout, or dial the hosted referee
   `wss://wotr.behindmedia.com/referee` with a match's seat token (README, "A hosted referee"):
   `python3 random_bot.py --connect wss://wotr.behindmedia.com/referee --token wotr_seat_…`. To play people, connect
   with a bot key instead (§14; README, "Play people on the site"); to play Lords of Middle-earth, declare it in the
   `hello`'s `rulesets` (§13).
3. Check your bot against the conformance games in [`conformance/`](conformance/): every decision there lists its
   options and the choice made, so a bot can be replayed through them.
