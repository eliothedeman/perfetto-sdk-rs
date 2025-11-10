use std::fs::File;
use tokio::time::{sleep, Duration};
use tracing::{info, info_span, instrument};
use tracing_perfetto_writer::PerfettoLayer;
use tracing_subscriber::prelude::*;

/// Simulates an async task with tracing
#[instrument]
async fn async_task(id: u32, duration_ms: u64) {
    info!("Task {} starting", id);
    sleep(Duration::from_millis(duration_ms)).await;
    info!("Task {} completed", id);
}

/// Demonstrates parallel async operations
async fn parallel_operations() {
    let _span = info_span!("parallel_operations").entered();

    // Spawn multiple tasks concurrently
    let handles = vec![
        tokio::spawn(async_task(1, 100)),
        tokio::spawn(async_task(2, 150)),
        tokio::spawn(async_task(3, 80)),
    ];

    // Wait for all tasks to complete
    for handle in handles {
        handle.await.expect("Task failed");
    }
}

/// Demonstrates sequential async operations
async fn sequential_operations() {
    let _span = info_span!("sequential_operations").entered();

    async_task(10, 50).await;
    async_task(11, 70).await;
    async_task(12, 60).await;
}

/// A more complex example with nested async operations
#[instrument]
async fn fetch_and_process(resource_id: u32) {
    info!("Fetching resource {}", resource_id);

    {
        let _span = info_span!("fetch").entered();
        sleep(Duration::from_millis(50)).await;
    }

    {
        let _span = info_span!("validate").entered();
        sleep(Duration::from_millis(20)).await;
    }

    {
        let _span = info_span!("process").entered();
        sleep(Duration::from_millis(100)).await;
    }

    info!("Resource {} completed", resource_id);
}

async fn pipeline() {
    let _span = info_span!("pipeline").entered();

    for i in 0..3 {
        fetch_and_process(i).await;
    }
}

#[tokio::main]
async fn main() {
    // Create a file to write the Perfetto trace to
    let file = File::create("trace_async.pftrace").expect("Failed to create trace file");

    // Create the Perfetto layer
    let perfetto_layer = PerfettoLayer::new(file);

    // Create a subscriber with the Perfetto layer
    let subscriber = tracing_subscriber::registry().with(perfetto_layer.clone());

    // Set the subscriber as the global default
    tracing::subscriber::set_global_default(subscriber)
        .expect("Failed to set subscriber");

    // Run traced async operations
    {
        let _span = info_span!("main").entered();
        info!("Async application started");

        parallel_operations().await;
        sequential_operations().await;
        pipeline().await;

        info!("Async application finished");
    }

    // Flush the trace to ensure all events are written
    perfetto_layer.flush().expect("Failed to flush trace");

    println!("Trace written to trace_async.pftrace");
    println!("View it at: https://ui.perfetto.dev/");
}
