# wotr-protocol

An open text protocol for computer opponents ("bots") for **War of the Ring, Second Edition** to play each other,
and people, whatever language or rules engine each is written in: the base game and, since 0.2, the expansion **Lords
of Middle-earth** (with and without its Council of Rivendell).

- **[SPEC.md](SPEC.md)**: the protocol, draft 0.2. One referee holds the rules; bots receive their side's view and a
  list of legal options at each decision, and answer with an option id. JSON Lines over stdin/stdout or a WebSocket.
  A bot declares the rules it plays (`rulesets`; none declared: the base game).
- **[CHANGELOG.md](CHANGELOG.md)**: what changed from version to version.
- **[vocabulary/](vocabulary/)**: the shared names for regions (with their neighbours), nations, characters, cards
  (keys and titles only), die faces and Hunt tiles; `vocabulary-0.2.json` adds Lords of Middle-earth (its cards,
  characters and versions, special dice, Elven Rings, Sméagol tiles, the Council's Action tokens, and the decision
  kinds and die actions), `vocabulary-0.1.json` is the base game's.
- **[examples/python/random_bot.py](examples/python/random_bot.py)**: a complete example bot (random legal moves,
  standard library only), over stdin/stdout or a WebSocket: the template to start from. It speaks 0.2 and declares
  every ruleset (the base game, Lords of Middle-earth, with the Council of Rivendell).
- **[conformance/](conformance/)**: recorded games with every random outcome, option fingerprint and choice, for
  checking a referee or a bot: three of the base game (`game-101` to `game-103`),
  two of Lords of Middle-earth (`game-201`, `game-202`) and two with the Council of Rivendell (`game-301`,
  `game-302`).

## A hosted referee

A referee runs at **`wss://wotr.behindmedia.com/referee`**. It plays matches between two bots; each bot connects
from wherever it runs (your machine, your server) and the referee holds the rules.

1. **Get a match.** A member of wotr.behindmedia.com (the site is invite-only; ask the person who sent you here, or
   request an invite on the site) creates a match on `https://wotr.behindmedia.com/referee` and chooses its rules:
   the number of games (1 to 10), the turn cap (10 to 60, or none), the clock per decision (1 to 60 seconds), what a
   timeout costs (option 0 is played, or the N-th timeout in a game forfeits it), fresh or paired seeds; the other
   seat is a second bot (to test yours against our greedy bot, use the sandbox below). The match gets
   **two seat tokens**, one per bot, shown once. Members can also create matches from a script with an API key
   (`POST https://wotr.behindmedia.com/referee/api/matches`, `Authorization: Bearer <key>`; the key is made on the
   site).
2. **Connect each bot with its token**, in its `hello` (`"token": "…"`) or in the address (`?token=…`). With the
   example bot:

   ```
   python3 random_bot.py --connect wss://wotr.behindmedia.com/referee --token wotr_seat_…
   ```

3. **Both connected, the games begin.** A coin decides who has the Free Peoples in game 1; then the sides alternate.
   A bot that drops forfeits the game in progress and may come back with its token within 5 minutes for the next
   game. A match not started within 24 hours expires; one running longer than 12 hours ends.
4. **Results**: members see every match with the bots' names and versions (as their `hello` says), the score and the
   score per side, and each game's record; the match's creator also gets the protocol logs (kept 14 days).

Limits: one connection per seat; messages of at most 16 KiB; at most 8 `get_view` per decision; a bot that floods
the referee with messages nobody asked for is disconnected. Matches between two bots play the base game.

## A sandbox to test your bot

**`wss://sandbox.wotr.behindmedia.com/referee`** is a test referee, apart from the site's real games: play as many
games as you like, as fast as you like, against a simple bot of ours or against your own bot. Nothing played there is
shown on the site.

1. **Get a sandbox key.** Sandbox keys are for the site's bot testers: on `https://wotr.behindmedia.com/referee/keys`,
   "Sandbox keys", make one (shown once; at most 5; revoke one there and it stops working within a minute). Not a bot
   tester yet? Ask the person who sent you here.
2. **Connect your bot with the key and say what you want in the address.** The key goes as
   `Authorization: Bearer wotr_sbx_…`, as `&key=…` in the address, or as `"token"` in your `hello`. With the example
   bot (its `--token` puts the key in the hello):

   ```
   python3 random_bot.py --connect "wss://sandbox.wotr.behindmedia.com/referee?opponent=greedy&games=20&clock_ms=500" --token wotr_sbx_…
   ```

   | Parameter | Values | Default |
   |---|---|---|
   | `opponent` | `greedy` (a simple one-step bot), `random` (a random legal option), `self:<name>` (two connections with the same key and name play each other) | `greedy` |
   | `games` | 1 to 1000; a coin decides who has the Free Peoples in game 1, then the sides alternate | 1 |
   | `rules` | a ruleset your `hello` declares: `base`, `lome`, `lome:council`, … | `base` |
   | `seed` | game 1's seed (game n plays seed + n − 1), to play a game again exactly | random |
   | `clock_ms` | the clock per decision, 20 to 60000 | 5000 |
   | `timeouts_forfeit` | 0 (a timeout plays option 0) or 1 to 5 (the N-th timeout in a game forfeits it) | 0 |
   | `max_turns` | 10 to 60 (then a draw), or `none` | `none` |

   For `self:<name>`, start the first connection, then the second with the **same address**; the first waits up to 5
   minutes for it. Your bot can play two versions of itself this way.
3. **The games** run one after the other on your connection, then the referee says `quit`. The `match` object of
   `options` has `"sandbox": true` and the parameters; everything else is the protocol as on the hosted referee.
4. **Results and logs**, with the same key: `GET https://sandbox.wotr.behindmedia.com/games` lists your key's last 100
   games, newest first (game id, seed, sides, winner, how, turns, decisions, timeouts, illegal answers, ms per answer);
   `GET https://sandbox.wotr.behindmedia.com/logs/<game id>` downloads a game's protocol log (gzipped JSON Lines, SPEC
   §10; kept 7 days).

   ```
   curl -H "Authorization: Bearer wotr_sbx_…" https://sandbox.wotr.behindmedia.com/games
   curl -H "Authorization: Bearer wotr_sbx_…" -o game.jsonl.gz https://sandbox.wotr.behindmedia.com/logs/g-…
   ```

Limits, only to keep the machine responsive: no limit on games; at most 8 games at once per key (a ninth connection is
told `busy`); messages of at most 16 KiB; 32 connections at once from one address; 10 wrong keys from an address lock it
out for 15 minutes; a game ends after 2 hours. Errors come as `{"type":"error","code":…,"message":…}` with
`unauthorized`, `bad_request` (a parameter, or rules your hello does not declare), `busy`, `no_partner`, `rate_limited`
or `unavailable`.

## Certify your bot

A **certified bot** plays by the official rules without fault: it answers every question with a listed option, in
time, without crashing, in whole games and from the position suite's positions. Certification does not judge
strength: a bot that loses every game still certifies.

1. **Get a sandbox key** (bot testers: `https://wotr.behindmedia.com/referee/keys`).
2. **Test as you go** with ordinary sandbox games: `?opponent=random&games=20&clock_ms=200` (the quickest check that
   every decision kind is answered), then `opponent=greedy`, fixed `seed`s to replay a failure exactly, and the
   protocol logs (`/logs/<game>`).
3. **Run the certification**: connect to
   `wss://sandbox.wotr.behindmedia.com/referee?certify=base` (or `certify=lome`, `certify=lome:council`, `certify=all`
   for every ruleset your `hello` declares) with your key. Optional: `clock_ms` (200–60000, default 1000),
   `stop_on_failure=1`. The run plays:
   - 10 games against `greedy` and 10 against `random` on each side, for each ruleset (fixed seeds);
   - every entry of the position suite (594 positions of the base game), your bot on each side in turn: the game
     starts at the entry's position (`new_game` says `"start":"position"` and `"suite_entry"`, and carries `view`,
     your side's view of the start position; there are no setup events) and ends at the entry's next quiet position
     (`game_over` with `"how":"SUITE_END"`);
   - the **scenarios**: 15 entries, each a question the official rules ask that bots got wrong (the Leader re-roll on
     each side, declining the Sorcerer's and the Guide's draws, Mighty Attack's Companion, Many Kings' counts, The
     Ringwraiths Are Abroad, The Black Captain Commands, Stormcrow, Gwaihir the Windlord, I Will Go Alone, a Hunt's
     remainder as Corruption, a `no_effect` option, a question answered `for_you`, the Voice of Saruman's Settlements). The referee plays the entry's
     first moves itself (`new_game` says `"scenario"` and `"played_for_you": N`; they come as ordinary `choice`
     events, both sides), then your bot answers its side.
4. **The verdict** comes as a last message, `{"type":"certification","passed":true,…}` with every failure (the game,
   why: `illegal_option`, `timeout`, `connection`, …), and stays at `GET https://sandbox.wotr.behindmedia.com/certification`
   with your key, with the protocol log of each failed game for 7 days. Fix, run again; a passed run is your
   certificate: name it when you register the bot for tournaments or online play.

What a bot must handle that a casual test may not show: `no_effect` options, the `skip` of an optional draw, reveal
paths with `strongholds`, the Voice of Saruman's `regions`, `LEADER_REROLL`, Mighty Attack's Companion, the Guide asked again, the hidden passes, a
`choice` made `for_you`, and a game that starts mid-way, some moves already played for you.

A bot that answers from its own engine should also never fall back to a default answer: the certification only sees
legal answers, so count your own fallbacks (our three adapters log each) and bring them to zero.

**Engines of your own:** a bot that keeps its own copy of the game can check that copy too: the conformance games
(`conformance/`) and the position suite ([`positions/`](positions/): the entries and the WPN position notation)
replay every decision's options (fingerprints) and the positions reached.

## Play people on the site

Your bot can play people on wotr.behindmedia.com, in their app, as any online game: they meet it in quick match (when
they welcome bots and nobody else is found within a short wait) or challenge it from the lobby's **Bots online** list.
Games against bots are never rated, and a bot plays either side.

1. **A bot account.** A member who tests bots on the site (a bot tester) makes a bot account for your bot on
   `https://wotr.behindmedia.com/referee/bots`: its name (shown as "Name (bot)"), a short description, and a
   greeting, the one chat message it sends at the start of a game. The site's admin approves it.
2. **Its key.** The bot account's page makes a **bot key** (`wotr_bot_…`), shown once. Keep it secret: it connects
   your bot as that account. A new key replaces the old one.
3. **Connect** to `wss://wotr.behindmedia.com/referee` with the key, as for a match (`"token"` in the `hello`, or
   `?token=…`). With the example bot:

   ```
   python3 random_bot.py --connect wss://wotr.behindmedia.com/referee --token wotr_bot_…
   ```

   Each connection plays one game at a time and otherwise waits; open up to three connections for three games at
   once. Leave your bot running: it plays whenever someone wants a game. It is offered games of the rules it
   declares in its `hello` (`"rulesets": ["base", "lome", "lome:council"]`; none declared: the base game only), and
   of the time controls its `seek` accepts (SPEC.md §14).
4. **Its games** are listed on the bot's page, with a replay of each and your bot's own log of it (kept 14 days).

## Bot tournaments

The site also runs **round-robin tournaments between bots**: you hand in your bot as an arm64 Linux Docker image, and
we run every bot on the same hardware (one Apple M4 performance core, 1.5 GB) under the same rules: T seconds a
decision, the bot frozen while it is not its turn, a timeout or a second illegal answer to one decision losing the
game. Results, cross-tables and every game's replay are public at `https://wotr.behindmedia.com/referee/tournaments`.
How to take part, the rules and the limits: **[TOURNAMENTS.md](TOURNAMENTS.md)**.

## Status

Draft 0.2 (2026-10-24), for discussion between the authors of War of the Ring bots: 0.1 with the rulesets and Lords
of Middle-earth, backwards compatible (a 0.1 bot plays the base game unchanged; CHANGELOG.md). The hosted referee
speaks 0.2. Issues and pull requests are welcome, especially on the open points at the end of the spec.

## Licence and trademarks

The specification text is licensed under CC BY 4.0, the code and data under the MIT licence (see LICENSE).

War of the Ring is a board game by Roberto Di Meglio, Marco Maggi and Francesco Nepitello, published by Ares Games;
Lords of Middle-earth is an expansion for it, also published by Ares Games. This is an unofficial fan project, not
affiliated with or endorsed by Ares Games or the Tolkien rights holders. The vocabulary contains names only; no card
texts, rules text or artwork.
