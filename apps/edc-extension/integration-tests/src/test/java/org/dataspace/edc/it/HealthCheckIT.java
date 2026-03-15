package org.dataspace.edc.it;

import org.junit.jupiter.api.Test;
import org.eclipse.edc.spi.system.ServiceExtension;

import java.util.ServiceLoader;
import java.util.Set;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * SPI discoverability check for the optional EDC runtime glue.
 * This is the strongest integration signal available until an embedded
 * connector-runtime harness is wired into apps/edc-extension.
 */
class HealthCheckIT {

    @Test
    void extensionModulesAreDiscoverableViaSpi() {
        Set<String> discoveredExtensions = ServiceLoader.load(ServiceExtension.class)
                .stream()
                .map(ServiceLoader.Provider::get)
                .map(ServiceExtension::name)
                .collect(Collectors.toSet());

        assertThat(discoveredExtensions).contains(
                "Dataspace Common Extension",
                "Dataspace Control-Plane Extension",
                "Dataspace Policy Functions",
                "Dataspace Participant Context",
                "Dataspace Management Webhooks",
                "Dataspace Contract Lifecycle Listener",
                "Dataspace Data-Plane Extension",
                "Dataspace HTTP Transfer Decorators",
                "Dataspace AAS Bridge",
                "Dataspace Transfer Observer",
                "Dataspace OIDC Auth Extension",
                "Dataspace Custom Web Contexts"
        );
    }
}
