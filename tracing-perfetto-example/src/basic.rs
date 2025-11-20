use std::fs::File;
use std::thread;
use std::time::Duration;
use tracing::{info, info_span};
use tracing_perfetto_writer::PerfettoLayer;
use tracing_subscriber::prelude::*;

/// Simulates some work being done
fn do_work(name: &str, duration_ms: u64) {
    let _span = info_span!("work", task = name).entered();
    info!("Starting work");
    thread::sleep(Duration::from_millis(duration_ms));
    info!("Finished work");
}

/// Demonstrates nested spans
fn complex_operation() {
    let _span = info_span!("complex_operation").entered();

    {
        let _span = info_span!("phase_1").entered();
        do_work("initialization", 50);
    }

    {
        let _span = info_span!("phase_2").entered();
        do_work("processing", 100);
    }

    {
        let _span = info_span!("phase_3").entered();
        do_work("finalization", 30);
    }
}

fn main() {
    // Create the Perfetto layer
    let perfetto_layer = PerfettoLayer::new();

    // Create a subscriber with the Perfetto layer
    let subscriber = tracing_subscriber::registry().with(perfetto_layer.clone());

    // Set the subscriber as the global default
    tracing::subscriber::set_global_default(subscriber).expect("Failed to set subscriber");

    // Run some traced operations
    {
        let _span = info_span!("main").entered();
        info!("Application started");

        do_work("task_1", 80);
        do_work("task_2", 120);

        complex_operation();

        info!("Application finished");
    }

    // Flush the trace to ensure all events are written
    let trace_data = perfetto_layer.flush().expect("Failed to flush trace");

    // Write the trace data to a file
    let mut file = File::create("trace_basic.pftrace").expect("Failed to create trace file");
    use std::io::Write as _;
    file.write_all(&trace_data)
        .expect("Failed to write trace data");

    println!("Trace written to trace_basic.pftrace");
    println!("View it at: https://ui.perfetto.dev/");
}
