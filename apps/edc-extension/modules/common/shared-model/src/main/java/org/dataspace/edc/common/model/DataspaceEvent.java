package org.dataspace.edc.common.model;

import java.time.Instant;
import java.util.Map;

/**
 * Generic event envelope emitted by EDC lifecycle listeners.
 * Forwarded to control-api via webhook callback.
 */
public record DataspaceEvent(
    String eventType,
    String resourceId,
    TenantId tenantId,
    Instant occurredAt,
    Map<String, Object> payload
) {}
