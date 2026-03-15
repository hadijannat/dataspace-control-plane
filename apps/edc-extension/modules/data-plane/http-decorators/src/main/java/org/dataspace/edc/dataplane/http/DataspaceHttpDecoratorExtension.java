package org.dataspace.edc.dataplane.http;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Decorates outbound HTTP transfer requests with dataspace-specific headers:
 * - X-Dataspace-Tenant-Id
 * - X-Dataspace-Agreement-Id
 * - X-Dataspace-Transfer-Id
 *
 * Uses EDC's HttpRequestParamsProvider SPI rather than patching the transport layer directly.
 * Per EDC official guidance: decorate via HttpRequestParamsProvider, not by modifying HTTP internals.
 */
@Extension(value = DataspaceHttpDecoratorExtension.NAME)
public class DataspaceHttpDecoratorExtension implements ServiceExtension {

    public static final String NAME = "Dataspace HTTP Transfer Decorators";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized");
        // TODO: register HttpRequestParamsProvider implementation when data-plane-http SPI is available
    }
}
