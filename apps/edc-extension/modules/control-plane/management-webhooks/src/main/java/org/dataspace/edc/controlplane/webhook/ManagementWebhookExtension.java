package org.dataspace.edc.controlplane.webhook;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Setting;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Forwards EDC management-plane events to control-api via HTTP webhook.
 * Covered events: contract negotiation state changes, transfer state changes, catalog updates.
 * Uses EDC Config API for endpoint — never hardcoded.
 */
@Extension(value = ManagementWebhookExtension.NAME)
public class ManagementWebhookExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Management Webhooks";

    @Setting(value = "control-api webhook endpoint URL", required = true)
    public static final String SETTING_WEBHOOK_URL = "dataspace.management.webhook.url";

    @Setting(value = "Shared secret for webhook HMAC validation", required = false)
    public static final String SETTING_WEBHOOK_SECRET = "dataspace.management.webhook.secret";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        var url = context.getSetting(SETTING_WEBHOOK_URL, null);
        context.getMonitor().info(NAME + " initialized — webhook URL: " + url);
        // TODO: register EDC event listeners and wire HTTP webhook emitter
    }
}
