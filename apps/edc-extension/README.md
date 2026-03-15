# apps/edc-extension

Eclipse Dataspace Connector (EDC) extension modules for the dataspace control plane.

## Modules

| Module | Purpose |
|--------|---------|
| `modules/common` | Shared utilities and marker service; required by all other modules |
| `modules/control-plane` | Policy functions, catalog augmentors, negotiation hooks |
| `modules/data-plane` | Transfer process listeners and data flow hooks |
| `modules/auth` | OIDC token validation for EDC API endpoints |
| `integration-tests` | Extension integration tests using embedded EDC runtime |

## Architecture Rules

- **No business logic**: All domain logic lives in `core/`. These modules are thin EDC wiring only.
- **EDC DI**: Use `@Extension`, `@Provides`, `@Inject`, `@Requires` for all dependencies.
- **Config API**: Read all runtime settings via EDC's `ServiceExtensionContext.getSetting()`. Never hardcode.
- **SPI JARs only**: Modules depend on `*-spi` artifacts; never on EDC internal implementation modules.
- **Discovery**: Each module registers its extension class in `META-INF/services/org.eclipse.edc.spi.system.ServiceExtension`.

## Build

```bash
./gradlew build
./gradlew test
./gradlew :integration-tests:test
```

## EDC Version

Currently scaffolded against EDC `0.7.0`. Update `gradle/libs.versions.toml` when upgrading.

## Validation Boundary

- Current integration coverage verifies SPI discoverability and extension packaging from inside `apps/edc-extension`.
- Full embedded-runtime smoke tests are still a follow-up dependency on an EDC runtime harness with stable test artifacts; keep business logic out of these modules until that harness exists.
