package org.dataspace.edc.common;

/**
 * Marker service registered by DataspaceExtension.
 * Downstream modules depend on this to signal common extension is loaded.
 */
public class DataspaceExtensionService {
    public String getVersion() {
        return "0.1.0-SNAPSHOT";
    }
}
