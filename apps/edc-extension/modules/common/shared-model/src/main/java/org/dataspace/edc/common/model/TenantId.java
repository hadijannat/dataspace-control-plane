package org.dataspace.edc.common.model;

/**
 * Typed value object for a dataspace tenant identifier.
 * Used as a typed header/parameter across all extension modules.
 */
public record TenantId(String value) {
    public TenantId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("TenantId must not be blank");
        }
    }

    @Override
    public String toString() {
        return value;
    }
}
