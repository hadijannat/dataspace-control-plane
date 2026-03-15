package org.dataspace.edc.testing;

import java.util.ArrayList;
import java.util.List;

/**
 * Builder for a test EDC connector instance with Dataspace extensions pre-loaded.
 * Use in integration tests to stand up an in-process connector.
 *
 * Usage:
 *   var connector = DataspaceConnectorBuilder.create()
 *       .withExtension(new DataspaceControlPlaneExtension())
 *       .build();
 */
public class DataspaceConnectorBuilder {

    private final List<Object> extensions = new ArrayList<>();

    private DataspaceConnectorBuilder() {}

    public static DataspaceConnectorBuilder create() {
        return new DataspaceConnectorBuilder();
    }

    public DataspaceConnectorBuilder withExtension(Object extension) {
        extensions.add(extension);
        return this;
    }

    /**
     * Build and start the embedded connector.
     * Returns a handle for querying/teardown.
     * TODO: wire to EDC's EmbeddedRuntime once connector runtime test artifacts are available.
     */
    public DataspaceConnectorHandle build() {
        return new DataspaceConnectorHandle(List.copyOf(extensions));
    }
}
