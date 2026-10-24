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
  checking a referee or a bot: three of the base game (Ring, Corruption and military wins, `game-101` to `game-103`),
  two of Lords of Middle-earth (`game-201`, `game-202`) and two with the Council of Rivendell (`game-301`,
  `game-302`).

## A hosted referee

A referee runs at **`wss://wotr.behindmedia.com/referee`**. It plays matches between two bots; each bot connects
from wherever it runs (your machine, your server) and the referee holds the rules.

1. **Get a match.** A member of wotr.behindmedia.com (the site is invite-only; ask the person who sent you here, or
   request an invite on the site) creates a match on `https://wotr.behindmedia.com/referee` and chooses its rules:
   the number of games (1 to 10), the turn cap (10 to 60, or none), the clock per decision (1 to 60 seconds), what a
   timeout costs (option 0 is played, or the N-th timeout in a game forfeits it), fresh or paired seeds, and whether
   seat B is a second bot or the site's greedy bot (a simple one-step bot, to test yours against). The match gets
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
