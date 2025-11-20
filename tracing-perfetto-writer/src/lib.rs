use perfetto_writer::{Context, EventBuilder};
use std::sync::{Arc, Mutex};
use tracing::field::Visit;
use tracing::{Subscriber, span};
use tracing_subscriber::{Layer, layer::Context as LayerContext, registry::LookupSpan};

#[derive(Debug, Clone, Copy)]
struct SliceId(u64);

impl Into<u64> for SliceId {
    fn into(self) -> u64 {
        self.0
    }
}

impl From<u64> for SliceId {
    fn from(value: u64) -> Self {
        Self(value)
    }
}

#[derive(Debug, Clone, Copy)]
struct TrackId(u64);

impl Into<u64> for TrackId {
    fn into(self) -> u64 {
        self.0
    }
}

impl From<u64> for TrackId {
    fn from(value: u64) -> Self {
        Self(value)
    }
}

struct EventBuilderVisitor<'a>(EventBuilder<'a>);

impl<'a> Visit for EventBuilderVisitor<'a> {
    fn record_debug(&mut self, field: &tracing::field::Field, value: &dyn std::fmt::Debug) {
        self.0.debug_str(field.name(), &format!("{:?}", value));
    }
}

/// A tracing layer that writes trace events to Perfetto format
pub struct PerfettoLayer {
    context: Arc<Mutex<Context>>,
}

impl Clone for PerfettoLayer {
    fn clone(&self) -> Self {
        Self {
            context: Arc::clone(&self.context),
        }
    }
}

impl PerfettoLayer {
    /// Creates a new PerfettoLayer
    pub fn new() -> Self {
        let ctx = Context::new();

        Self {
            context: Arc::new(Mutex::new(ctx)),
        }
    }

    /// Flushes the underlying Perfetto context to a Vec
    pub fn flush(&self) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        let mut buf = Vec::new();
        self.context.lock().unwrap().write_to(&mut buf)?;
        Ok(buf)
    }
}

impl<S> Layer<S> for PerfettoLayer
where
    S: Subscriber + for<'a> LookupSpan<'a>,
{
    fn on_new_span(&self, attrs: &span::Attributes<'_>, id: &span::Id, ctx: LayerContext<'_, S>) {
        let mut context = self.context.lock().unwrap();
        let thread_track: TrackId = context.current_thread_track().into();
        let slice_id: SliceId = context.next_id().into();
        if let Some(span) = ctx.span(id) {
            let mut exe = span.extensions_mut();
            exe.insert(thread_track);
            exe.insert(slice_id);
            let meta = span.metadata();
            let mut ev = EventBuilderVisitor(
                context
                    .event()
                    .with_begin()
                    .with_track_uuid(thread_track.into())
                    .with_flow_id(slice_id.0)
                    .with_source_location(
                        meta.file().unwrap_or_default(),
                        meta.line().unwrap_or_default(),
                    )
                    .with_now()
                    .with_category(meta.level().as_str())
                    .with_name(attrs.metadata().name()),
            );
            if let Some(parent) = span.parent() {
                if let Some(parent_slice) = parent.extensions().get::<SliceId>() {
                    ev.0.flow_id(parent_slice.0);
                }
            }
            attrs.record(&mut ev);
            ev.0.build();
        }
    }

    // fn on_enter(&self, id: &span::Id, ctx: LayerContext<'_, S>) {
    //     let mut context = self.context.lock().unwrap();
    //     if let Some(span) = ctx.span(id) {
    //         let exe = span.extensions();
    //         let track = exe.get::<TrackId>().unwrap();
    //         context
    //             .event()
    //             .begin()
    //             .now()
    //             .track_uuid((*track).into())
    //             .name("active")
    //             .build();
    //     }
    // }

    // fn on_exit(&self, id: &span::Id, ctx: LayerContext<'_, S>) {
    //     let mut context = self.context.lock().unwrap();
    //     if let Some(span) = ctx.span(id) {
    //         let exe = span.extensions();
    //         let track = exe.get::<TrackId>().unwrap();
    //         context
    //             .event()
    //             .end()
    //             .now()
    //             .track_uuid((*track).into())
    //             .name("active")
    //             .build();
    //     }
    // }

    fn on_close(&self, id: span::Id, ctx: LayerContext<'_, S>) {
        let mut context = self.context.lock().unwrap();
        if let Some(span) = ctx.span(&id) {
            let exe = span.extensions();
            let track = exe.get::<TrackId>().unwrap();
            context
                .event()
                .with_end()
                .with_now()
                .with_track_uuid((*track).into())
                .with_name(span.name())
                .build();
        }
    }

    fn on_event(&self, event: &tracing::Event<'_>, ctx: LayerContext<'_, S>) {
        let mut context = self.context.lock().unwrap();
        if let Some(span) = ctx.event_span(event) {
            let exe = span.extensions();
            let track = exe.get::<TrackId>().unwrap();
            let meta = event.metadata();
            let mut ev = EventBuilderVisitor(
                context
                    .event()
                    .with_instant()
                    .with_now()
                    .with_track_uuid((*track).into())
                    .with_category(meta.target())
                    .with_source_location(
                        meta.file().unwrap_or_default(),
                        meta.line().unwrap_or_default(),
                    )
                    .with_category(meta.level().as_str())
                    .with_name(event.metadata().name()),
            );
            event.record(&mut ev);
            ev.0.build();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tracing_subscriber::prelude::*;

    #[test]
    fn test_layer_creation() {
        let layer = PerfettoLayer::new();
        // Just ensure it compiles and creates successfully
        drop(layer);
    }

    #[test]
    fn test_layer_with_subscriber() {
        let layer = PerfettoLayer::new();

        let subscriber = tracing_subscriber::registry().with(layer);

        // Set as default and create a span
        tracing::subscriber::with_default(subscriber, || {
            let span = tracing::info_span!("test_span");
            let _enter = span.enter();
            tracing::info!("test event");
        });
    }
}
