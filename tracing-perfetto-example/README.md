# tracing-perfetto-writer Example

This crate demonstrates how to use `tracing-perfetto-writer` to record application traces in Perfetto format.

## Examples

### Basic Example

The `basic` example demonstrates:
- Setting up the Perfetto layer with tracing
- Creating simple spans
- Nested span operations
- Instant events
- Writing traces to a file

Run with:
```bash
cargo run --bin basic
```

This will generate `trace_basic.pftrace` that can be viewed at https://ui.perfetto.dev/

### Async Tasks Example

The `async_tasks` example demonstrates:
- Using tracing with async/await (tokio)
- Parallel async operations
- Sequential async operations
- Complex nested async workflows
- Using the `#[instrument]` macro

Run with:
```bash
cargo run --bin async_tasks
```

This will generate `trace_async.pftrace` that can be viewed at https://ui.perfetto.dev/

## Viewing Traces

1. Run one of the examples to generate a `.pftrace` file
2. Open https://ui.perfetto.dev/ in your browser
3. Click "Open trace file" and select the generated `.pftrace` file
4. Explore your application's timing and trace data visually

## Features Demonstrated

- **Span creation**: Using `info_span!()` to create traced spans
- **Span entry/exit**: Using `.entered()` to track when spans are active
- **Instant events**: Using `info!()` and other event macros
- **Nested spans**: Creating hierarchies of operations
- **Async tracing**: Tracing across async/await boundaries
- **Instrumentation macro**: Using `#[instrument]` for automatic span creation
- **Flush control**: Explicitly flushing traces to disk
