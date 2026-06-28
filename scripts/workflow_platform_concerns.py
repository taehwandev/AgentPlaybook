"""Platform-specific concern-to-document routes for workflow routing."""

from __future__ import annotations

from typing import Dict, Tuple


ANDROID_EXTERNAL_SKILL_DOCS = ("platforms/android/android-external-skill-source-coverage.md",)
ANDROID_COMPOSE_DOCS = (
    "platforms/android/android-compose-ui.md",
    "platforms/android/android-review.md",
    *ANDROID_EXTERNAL_SKILL_DOCS,
)
ANDROID_STRUCTURE_DOCS = (
    "platforms/android/android-module-structure.md",
    *ANDROID_EXTERNAL_SKILL_DOCS,
)
ANDROID_PLATFORM_SURFACE_DOCS = (
    "platforms/android/android-module-structure.md",
    "platforms/android/android-review.md",
    *ANDROID_EXTERNAL_SKILL_DOCS,
)
ANDROID_PERSISTENCE_DOCS = (
    "platforms/android/android-state-data.md",
    "platforms/android/references/android-datastore.md",
)


PLATFORM_CONCERNS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("android", "architecture"): (
        "platforms/android/android-architecture.md",
        "platforms/android/android-module-structure.md",
        *ANDROID_EXTERNAL_SKILL_DOCS,
    ),
    ("android", "security"): (
        "platforms/android/android-security.md",
        "platforms/android/android-review.md",
        *ANDROID_EXTERNAL_SKILL_DOCS,
    ),
    ("android", "compose"): ANDROID_COMPOSE_DOCS,
    ("android", "performance"): ANDROID_COMPOSE_DOCS,
    ("android", "state"): (
        "platforms/android/android-viewmodel-state.md",
        "platforms/android/android-compose-ui.md",
        *ANDROID_EXTERNAL_SKILL_DOCS,
    ),
    ("android", "ui"): ANDROID_COMPOSE_DOCS,
    ("android", "testing"): (
        "platforms/android/android-review.md",
        *ANDROID_EXTERNAL_SKILL_DOCS,
    ),
    ("android", "test"): (
        "platforms/android/android-review.md",
        *ANDROID_EXTERNAL_SKILL_DOCS,
    ),
    ("android", "structure"): ANDROID_STRUCTURE_DOCS,
    ("android", "module"): ANDROID_STRUCTURE_DOCS,
    ("android", "background"): ("platforms/android/android-background-work.md",),
    ("android", "cache"): ANDROID_PERSISTENCE_DOCS,
    ("android", "persistence"): ANDROID_PERSISTENCE_DOCS,
    ("android", "devtools"): ANDROID_PLATFORM_SURFACE_DOCS,
    ("android", "dependency"): ANDROID_PLATFORM_SURFACE_DOCS,
    ("android", "release"): ANDROID_PLATFORM_SURFACE_DOCS,
    ("android", "migration"): ANDROID_PLATFORM_SURFACE_DOCS,
    ("android", "platform"): ANDROID_PLATFORM_SURFACE_DOCS,
    ("kmp", "security"): ("platforms/kmp/kmp-security.md",),
    ("kmp", "compose"): ("platforms/kmp/kmp-compose-ui.md",),
    ("kmp", "state"): ("platforms/kmp/kmp-state-data.md",),
    ("kmp", "ui"): ("platforms/kmp/kmp-compose-ui.md",),
    ("kmp", "structure"): ("platforms/kmp/kmp-module-structure.md",),
    ("kmp", "module"): ("platforms/kmp/kmp-module-structure.md",),
    ("kmp", "platform"): ("platforms/kmp/kmp-platform-integration.md",),
    ("kmp", "desktop"): (
        "platforms/kmp/kmp-platform-integration.md",
        "platforms/application/application-command-ui.md",
        "platforms/application/application-system-integration.md",
    ),
    ("flutter", "security"): ("platforms/flutter/flutter-security.md",),
    ("flutter", "widget"): ("platforms/flutter/flutter-widget-ui.md",),
    ("flutter", "state"): ("platforms/flutter/flutter-state-data.md",),
    ("flutter", "ui"): ("platforms/flutter/flutter-widget-ui.md",),
    ("flutter", "structure"): ("platforms/flutter/flutter-project-structure.md",),
    ("flutter", "module"): ("platforms/flutter/flutter-project-structure.md",),
    ("flutter", "platform"): ("platforms/flutter/flutter-platform-integration.md",),
    ("flutter", "channel"): ("platforms/flutter/flutter-platform-integration.md",),
    ("swift", "architecture"): ("platforms/swift/swift-architecture.md",),
    ("swift", "structure"): ("platforms/swift/swift-code-structure.md",),
    ("swift", "module"): ("platforms/swift/swift-code-structure.md",),
    ("swift", "state"): ("platforms/swift/swift-architecture.md",),
    ("swift", "ui"): ("platforms/swift/swift-design-system.md",),
    ("swift", "design"): ("platforms/swift/swift-design-system.md",),
    ("swift", "design-system"): ("platforms/swift/swift-design-system.md",),
    ("swift", "tokens"): ("platforms/swift/swift-design-system.md",),
    ("ios", "security"): ("platforms/ios/ios-security.md",),
    ("ios", "architecture"): ("platforms/ios/ios-architecture.md",),
    ("ios", "swiftui"): ("platforms/ios/ios-swiftui-ui.md", "platforms/swift/swift-design-system.md"),
    ("ios", "uikit"): ("platforms/ios/ios-uikit-ui.md", "platforms/swift/swift-design-system.md"),
    ("ios", "state"): ("platforms/ios/ios-state-concurrency.md",),
    ("ios", "ui"): ("platforms/ios/ios-swiftui-ui.md", "platforms/swift/swift-design-system.md"),
    ("ios", "design"): ("platforms/swift/swift-design-system.md",),
    ("ios", "design-system"): ("platforms/swift/swift-design-system.md",),
    ("ios", "tokens"): ("platforms/swift/swift-design-system.md",),
    ("ios", "structure"): ("platforms/ios/ios-module-structure.md",),
    ("ios", "module"): ("platforms/ios/ios-module-structure.md",),
    ("web", "accessibility"): ("platforms/web/web-accessibility-i18n.md",),
    ("web", "react"): ("platforms/web/web-react-ui.md",),
    ("web", "state"): ("platforms/web/web-state-data.md",),
    ("web", "api"): ("platforms/web/web-state-data.md", "platforms/web/web-security.md"),
    ("web", "cache"): ("platforms/web/web-state-data.md", "platforms/web/web-security.md"),
    ("web", "persistence"): ("platforms/web/web-state-data.md", "platforms/web/web-security.md"),
    ("web", "auth"): ("platforms/web/web-state-data.md", "platforms/web/web-security.md"),
    ("web", "ui"): ("platforms/web/web-react-ui.md", "platforms/web/web-design-system.md"),
    ("web", "component"): ("platforms/web/web-react-ui.md", "platforms/web/web-design-system.md"),
    ("web", "component-api"): ("platforms/web/web-react-ui.md", "platforms/web/web-design-system.md"),
    ("web", "structure"): ("platforms/web/web-code-structure.md",),
    ("web", "security"): ("platforms/web/web-security.md",),
    ("server", "api"): ("platforms/server/server-api-implementation.md",),
    ("server", "security"): ("platforms/server/server-security.md",),
    ("application", "swift"): (
        "platforms/swift/swift-architecture.md",
        "platforms/swift/swift-code-structure.md",
        "platforms/swift/swift-design-system.md",
        "platforms/swift/swift-review.md",
    ),
    ("application", "architecture"): ("platforms/application/application-architecture.md",),
    ("application", "desktop"): (
        "platforms/application/application-react-desktop.md",
        "platforms/application/application-command-ui.md",
    ),
    ("application", "react"): (
        "platforms/application/application-react-desktop.md",
        "platforms/web/web-code-structure.md",
        "platforms/web/web-react-ui.md",
        "platforms/web/web-state-data.md",
    ),
    ("application", "ui"): ("platforms/application/application-command-ui.md",),
    ("application", "design"): ("platforms/swift/swift-design-system.md",),
    ("application", "design-system"): ("platforms/swift/swift-design-system.md",),
    ("application", "security"): ("platforms/application/application-security.md",),
}
