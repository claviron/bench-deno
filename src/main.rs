use std::path::PathBuf;

use clap::Parser;
use claviron::{FleetName, Server, ServerName, ServerOptions};

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

#[derive(Parser)]
#[command(about = "Standalone Claviron host for the shared Deno workload")]
struct Args {
    #[arg(long, default_value = "config")]
    config: PathBuf,
    #[arg(long, default_value = "bench-deno", value_parser = str::parse::<ServerName>)]
    name: ServerName,
    #[arg(long, default_value = "bdemo", value_parser = str::parse::<FleetName>)]
    fleet: FleetName,
    #[arg(long)]
    production: bool,
    #[arg(long)]
    check_config: bool,
}

#[tokio::main]
async fn main() -> claviron::Result<()> {
    let args = Args::parse();
    let mut options = ServerOptions::new()
        .config_dir(args.config)
        .name(args.name)
        .fleet_name(args.fleet);
    if args.production {
        options = options.production();
    }
    let server =
        Server::with_options(options).register(claviron_deno::register);
    if args.check_config {
        server.check_config().await
    } else {
        server.serve().await
    }
}
