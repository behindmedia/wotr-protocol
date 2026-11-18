# Bot tournaments

The site [wotr.behindmedia.com](https://wotr.behindmedia.com) runs round-robin tournaments between bots that speak the
[WotR Bot Protocol](SPEC.md). You hand in your bot as a Docker image; we run every bot on the same hardware, under the
same limits, and publish the results. This page tells you what you need to take part.

## In short

1. Build your bot as an **arm64 Linux Docker image**, at most **2 GB**, that connects to the address in
   `WOTR_REFEREE_URL` with the token in `WOTR_SEAT_TOKEN`, plays one game and exits.
2. Make the image downloadable: from a registry **by digest**, or as a `docker save` file at an https address.
3. Register it on the site (a member's login): **wotr.behindmedia.com/referee/tournament-bots**.
4. After the organiser approves it, it is fetched, checked and plays one short test game; you see the result on its page.
5. It is entered in an event, and the results appear on **wotr.behindmedia.com/referee/tournaments**.

## The format

- **Round robin:** every bot plays every other bot **2N games: N deals, each played from both sides** (the same seed,
  the sides swapped). That cancels much of the dice's and the cards' luck. N is set per event.
- **The base game** (2nd edition rules), unless an event says otherwise.
- **Scoring:** a win 1, a draw ½, a loss 0. **The turn cap** (40 by default, per event) reached is a draw.
- **Standings:** points, then Buchholz Cut 1, Buchholz, Sonneborn-Berger, the direct encounter, wins, wins as the Free
  Peoples. With them a cross-table, each bot's record per side, and how its games ended.

## Time

- **T seconds for every decision** (every kind of decision, battle choices and card answers included), stated in the
  `decide` message's clock (`per_decision`). **Unused time is not carried over.** T is set per event (typically 2 to 5 s).
- **No answer in time loses the game.**
- **Your bot is frozen while it is not its turn:** from its answer until its next decision the container is paused
  (every process stopped), so no bot can think on the opponent's time. Messages sent to it meanwhile (events,
  `game_over`) wait in its connection and arrive when it is thawed. **The clock starts only after the thaw**, so a
  frozen bot loses no time. A frozen bot is never pinged and never counted as disconnected.
- **Tip:** start your own timer when the `decide` arrives and answer with your best move so far shortly before the
  deadline. Our own bot keeps back a fixed 200 ms, which is ample on these machines (the answer travels over a local
  connection). Answer forced decisions (one option) at once. Don't rely on wall-clock time passing between your own
  decisions: the freeze stops it for you.

## Hardware and limits

Every bot gets exactly the same:

| | |
|---|---|
| CPU | **1 thread's worth** (one core's time, however many threads you start), on an Apple M4 performance core |
| Memory | **1.5 GB**, no swap |
| GPU | none |
| Network | **only the referee**: no internet, no other bot |
| Processes | at most 512 |
| Image | **at most 2 GB** uncompressed, `linux/arm64` |
| Storage | the container's own file system, discarded after each game |

Several games run at once on identical machines, each bot limited to its single core. Your bot's CPU use while
deciding, while frozen (should be nil) and its slow decisions are published, so the organiser can see that the
compute was fair.

## Your Docker image

- **Platform:** `linux/arm64`. Build with `docker build --platform linux/arm64 -t mybot:1.0 .`
- **Size:** at most 2 GB uncompressed (`docker image inspect` reports it as `Size`). A larger image is refused.
- **What it does:** its default command starts your bot, which reads two environment variables:

  | Variable | Contents |
  |---|---|
  | `WOTR_REFEREE_URL` | the referee's address, `ws://…` |
  | `WOTR_SEAT_TOKEN` | the token for this one seat of this one game |

  It connects to `WOTR_REFEREE_URL`, gives the token (as `?token=…` on the address, a bearer header, or `"token"` in
  its `hello`), plays **one game** and exits. One container per game: nothing carries over between games.
- **The session:** `hello`, `options` (with a `match` object: `tournament` true, the event's `id` and `name`,
  `game_number` of `games`, `clock_ms`, `max_turns`, `timeouts_forfeit` 1, `paired_seeds` true,
  `frozen_between_decisions` true), `new_game`, the game, `game_over`, `quit`. Everything else is [SPEC.md](SPEC.md).
- **A minimal example:**

  ```dockerfile
  FROM --platform=linux/arm64 python:3.12-slim
  COPY bot/ /bot
  CMD ["python", "/bot/main.py"]   # reads WOTR_REFEREE_URL and WOTR_SEAT_TOKEN
  ```

- **Labels (recommended):** they are part of the image and its digest, and the organiser picks bots from a list of the
  images with them, so they show which version plays (the organiser's list of the images on the machines shows each image with them, newest first):

  ```dockerfile
  LABEL org.opencontainers.image.title="mybot" \
        org.opencontainers.image.version="1.4.2" \
        org.opencontainers.image.revision="<your source commit>" \
        org.opencontainers.image.description="One line about the bot" \
        org.opencontainers.image.authors="Your name" \
        com.behindmedia.wotr.bot="My Bot" \
        com.behindmedia.wotr.owner="your username on the site" \
        com.behindmedia.wotr.engine="mybot-mcts 1.4.2" \
        com.behindmedia.wotr.config="2,000 playouts, 1 thread, 200 ms margin" \
        com.behindmedia.wotr.model="net-v7" \
        com.behindmedia.wotr.protocol="wotr-bot/0.2"
  ```

  `com.behindmedia.wotr.bot` is the name shown; `engine`, `config` and `model` say what plays (the program and its
  version, its settings, its networks or `none`); `protocol` the protocol version it speaks. None is required.

## How the image gets to us

No uploads and no registry passwords. Either:

- **A registry reference by digest**, from a registry that allows anonymous pulls, e.g.
  `ghcr.io/you/mybot@sha256:3f2a…` (after `docker push`, `docker inspect --format '{{index .RepoDigests 0}}' mybot:1.0`
  shows it), or
- **A file at an https address** with its SHA-256: `docker save mybot:1.0 | zstd > mybot.tar.zst`
  (`.tar`, `.tar.gz` or `.tar.zst`), for example a GitHub release asset, and `shasum -a 256 mybot.tar.zst`.

The digest or checksum guarantees that exactly what you handed in plays. Your image is kept private and is only run
for the events it is entered in.

## Registering

On **wotr.behindmedia.com/referee/tournament-bots** (a member's login): the bot's name, a contact, a short
description, and where to get the image. You may register for an event that is open for registration, or in general.

After the organiser approves it, the image is fetched and checked: the digest or checksum, the 2 GB limit,
`linux/arm64`, and **one short test game against our random bot** (5 s a decision, a few turns), which shows that it
starts, connects and answers. The result, and your bot's last output lines if something went wrong, appear on its page.
You can hand in a new version, or withdraw the bot, until its event starts. At most 5 bots per member at a time.

## What loses a game

| What happens | Result |
|---|---|
| No answer within the decision's time | **loss** (`FORFEIT`) |
| An illegal answer (not one of the options, a stale fingerprint) | an `error` and the question **asked again once**; a **second illegal answer to the same decision** loses |
| A malformed message | not an answer: the decision then times out |
| A crash, the connection closed, the process ended | **loss** |
| Not connecting in time (120 s after its start) or ending before connecting | the game is **played again later** (often the machine's doing); at its **third attempt** it counts as a loss |
| A failed handshake (a wrong `hello`) | **loss** |
| Reaching the turn cap | **draw** (`how` `TURN_CAP`, `winner` null), ½ each |
| A problem of ours (a machine restarting, a container removed from outside) | the game is **voided and played again**, never counted against you |

## Results

Public at **wotr.behindmedia.com/referee/tournaments** (and as JSON at `/referee/api/tournaments/{id}`):

- the standings, the cross-table, each bot's record as the Free Peoples and as the Shadow;
- **how each bot's games ended**: won on the board, won by the opponent's forfeit, drawn, lost on the board, lost by
  timeout, illegal answers, failing to connect, or a crash;
- per bot: decisions, thinking time per decision, its longest answers against the clock, CPU use while deciding and
  while frozen, slow decisions;
- every game's record and replay, once **both games of its deal** are over (the second game uses the same seed);
- the seeds, once the event is over.

## Testing your bot before you register

Any referee that speaks the protocol will do; ours is the site's hosted referee (`/referee`, see the README): play a
match against our greedy bot there, with a per-decision clock, to see that your bot answers every kind of decision
within its time. Then build the image and run it locally the way we will:

```sh
docker run --rm --platform linux/arm64 --cpus=1 --memory=1.5g --memory-swap=1.5g \
  -e WOTR_REFEREE_URL="wss://wotr.behindmedia.com/referee" -e WOTR_SEAT_TOKEN="<a seat token of your match>" mybot:1.0
```

## Questions

Open an issue in this repository.
