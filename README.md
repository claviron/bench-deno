# bench-deno

Compare Claviron's embedded Deno runtime with Deno's built-in HTTP server.
Both execute the same [Fetch handler](js/app.ts). The Claviron host contains
only the JavaScript runtime and defaults to one standalone process.

## Build

Use a stable Rust toolchain, Python 3 and the platform's V8 build prerequisites:

```sh
python3 scripts/build.py --native
```

To measure unreleased source, select both checkouts explicitly:

```sh
python3 scripts/build.py --native \
  --claviron-source /path/to/claviron-source \
  --deno-source /path/to/deno-source
```

The source overrides and build record stay under ignored `.cache/`.
The script preserves `PATH`, existing compiler flags and `CARGO_TARGET_DIR`.
When a target directory is supplied, use its `release/bench-deno` executable.

## Run

Run from the repository root. The supplied configuration declares **16 Deno
instances**, round-robin dispatch, admission capacity **2,048** and an isolate
command queue of **64**. Select a free loopback port and a test-only fleet name.
The embedded runtime uses Deno's Fetch Web APIs, matching the existing
application integration.

```sh
BENCH_LISTEN=127.0.0.1:8080 RUST_LOG=info \
  ./target/release/bench-deno --production --fleet bdemo
```

Add `--workers N` to run N supervised Claviron worker processes; `--workers 0`
is the standalone default. The `instances` value in `config/js.yaml` applies
to each serving process. For example, four workers with two instances each
run eight Deno isolates in total; the supervisor master hosts no isolates.

For native Deno, run the same module with 16 parallel workers:

```sh
DENO_JOBS=16 deno serve --parallel --host 127.0.0.1 --port 8080 js/app.ts
```

Run the servers sequentially. Verify that the chosen Deno release uses one
serving process with 16 JavaScript isolates. Each isolate emits one
`BENCH_DENO_READY` startup record; `/ready` returns its identity and counter.

| Path | Work |
| --- | --- |
| `/deno` | Read method, URL and body; encode JSON with a persistent counter. |
| `/deno/echo` | The same workload, also used for a Unicode POST preflight. |
| `/plain` | Return a fixed text response from JavaScript. |
| `/ready` | Observe the serving isolate outside timed load. |

## Measure

Use identical HTTP/1.1 keep-alive loads, warmup requests and response checks:

```sh
wrk -t32 -c128 -d5m --latency -s scripts/summary.lua http://127.0.0.1:8080/deno
wrk -t32 -c1024 -d5m --latency -s scripts/summary.lua http://127.0.0.1:8080/deno
```

The Lua callback runs only when a measurement finishes. Compare successful
requests/s, p99, errors and serving-process CPU time per completed request.
Record exact source revisions, Deno/V8 versions, effective configuration and
the instance count. Keep results in the run's issue; local artifacts belong
under ignored `.runs/`.

## License

MIT OR Apache-2.0; see [LICENSE-MIT](LICENSE-MIT) and
[LICENSE-APACHE](LICENSE-APACHE).
