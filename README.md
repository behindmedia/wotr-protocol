# wotr-protocol

An open text protocol for computer opponents ("bots") for **War of the Ring, Second Edition** to play each other,
whatever language or rules engine each is written in.

- **[SPEC.md](SPEC.md)**: the protocol, draft 0.1. One referee holds the rules; bots receive their side's view and a
  list of legal options at each decision, and answer with an option id. JSON Lines over stdin/stdout or a WebSocket.
- **[vocabulary/](vocabulary/)**: the shared names for regions (with their neighbours), nations, characters, cards
  (keys and titles only), die faces and Hunt tiles.
- **[examples/python/random_bot.py](examples/python/random_bot.py)**: a complete example bot (random legal moves,
  standard library only), over stdin/stdout or a WebSocket: the template to start from.
- **[conformance/](conformance/)**: three recorded games (Ring, Corruption and military wins) with every random
  outcome, option fingerprint and choice, for checking a referee or a bot.

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
the referee with messages nobody asked for is disconnected.

## Status

Draft for discussion between the authors of War of the Ring bots. Issues and pull requests are welcome, especially on
the open points at the end of the spec.

## Licence and trademarks

The specification text is licensed under CC BY 4.0, the code and data under the MIT licence (see LICENSE).

War of the Ring is a board game by Roberto Di Meglio, Marco Maggi and Francesco Nepitello, published by Ares Games.
This is an unofficial fan project, not affiliated with or endorsed by Ares Games or the Tolkien rights holders. The
vocabulary contains names only; no card texts, rules text or artwork.
