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

An open referee is coming at `wss://wotr.behindmedia.com/referee` (details in SPEC.md, "Transport"): connect your bot
to it to play against other bots. Until then, the example bots run over stdin/stdout against any local referee.

## Status

Draft for discussion between the authors of War of the Ring bots. Issues and pull requests are welcome, especially on
the open points at the end of the spec.

## Licence and trademarks

The specification text is licensed under CC BY 4.0, the code and data under the MIT licence (see LICENSE).

War of the Ring is a board game by Roberto Di Meglio, Marco Maggi and Francesco Nepitello, published by Ares Games.
This is an unofficial fan project, not affiliated with or endorsed by Ares Games or the Tolkien rights holders. The
vocabulary contains names only; no card texts, rules text or artwork.
