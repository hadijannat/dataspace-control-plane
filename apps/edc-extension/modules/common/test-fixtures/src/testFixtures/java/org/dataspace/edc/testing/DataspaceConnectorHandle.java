package org.dataspace.edc.testing;

import java.util.List;

/**
 * Handle to a running test connector instance.
 */
public class DataspaceConnectorHandle implements AutoCloseable {
    private final List<Object> extensions;

    DataspaceConnectorHandle(List<Object> extensions) {
        this.extensions = extensions;
    }

    public List<Object> getExtensions() {
        return extensions;
    }

    @Override
    public void close() {
        // teardown embedded connector
    }
}
