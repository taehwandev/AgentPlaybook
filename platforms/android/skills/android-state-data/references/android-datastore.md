---
keyflow_id: sys_android_datastore_reference
status: review
type: human-reviewed-needed
---

# Android DataStore Persistence

Use this reference when an Android task adds, reviews, or migrates Jetpack
DataStore persistence, persistent settings, user preferences, feature flags,
session metadata, cache metadata, or SharedPreferences replacement.

Official references:

- Android DataStore guide:
  `https://developer.android.com/topic/libraries/architecture/datastore`
- Preferences DataStore codelab:
  `https://developer.android.com/codelabs/android-preferences-datastore`

## Decision Matrix

Use one of these choices:

| Choice | Use When | Avoid When |
| --- | --- | --- |
| Preferences DataStore | Small key-value settings, toggles, enum preferences, migration from simple SharedPreferences. | The data needs schema/type safety, nested objects, versioned domain meaning, or many related fields. |
| Typed DataStore | One immutable settings object with a schema or serializer, such as Proto, JSON, or another explicit serializer. | The data needs relational queries, partial row updates, joins, or many independently updated entities. |
| Room, not DataStore | Large/complex datasets, queryable records, partial updates, referential integrity, relationships, history, or offline domain data. | The data is only a tiny settings object or preference flag. |

Do not add DataStore only because persistence is needed. First name the data
shape, lifetime, write frequency, query needs, migration path, and owner.

## Ownership

DataStore is a data-source implementation detail.

```text
View/Composable
  -> ViewModel Action
  -> UseCase when policy is real
  -> Repository API
  -> Repository implementation
  -> DataStore data source
  -> mapped repository/domain entity
  -> UiState and SideEffect
```

Rules:

- UI observes ViewModel state, not raw DataStore flows.
- ViewModel calls repository/use-case methods, not `DataStore.updateData`.
- Repository API exposes product entities or settings models, not
  `Preferences`, proto generated classes, serializers, files, or DataStore
  instances.
- DataStore creation lives in app/runtime/data DI or the repository
  implementation module.
- A reusable assertion fake should implement the repository/data-source API, not
  instantiate production DataStore unless the test specifically verifies
  DataStore integration.

## Module Placement

Typical split:

```text
settings-api/
  UserSettingsRepository.kt
  model/UserSettings.kt

settings-impl/
  UserSettingsRepositoryImpl.kt
  UserSettingsDataSource.kt
  UserSettingsSerializer.kt
  mapper/UserSettingsMapper.kt
  di/UserSettingsModule.kt

settings-assertions/
  RecordingUserSettingsRepository.kt
  UserSettingsFixtures.kt
```

Use `api` when another feature or test boundary needs a stable repository
contract. Use `impl` for DataStore, serializer, migration, corruption handler,
and mapping. Use `assertions` only when reusable fakes or fixtures are needed by
two or more test boundaries.

## Preferences DataStore

Use for small key-value state without a schema:

```kotlin
private val SORT_ORDER = stringPreferencesKey("sort_order")
private val SHOW_COMPLETED = booleanPreferencesKey("show_completed")

class UserPreferencesDataSource(
    private val dataStore: DataStore<Preferences>,
) {
    val settings: Flow<UserSettings> =
        dataStore.data.map { preferences ->
            UserSettings(
                sortOrder = SortOrder.fromStorage(preferences[SORT_ORDER]),
                showCompleted = preferences[SHOW_COMPLETED] ?: false,
            )
        }

    suspend fun setSortOrder(value: SortOrder) {
        dataStore.edit { preferences ->
            preferences[SORT_ORDER] = value.storageValue
        }
    }
}
```

Do not expose `Preferences` outside the data-source or repository
implementation. Convert missing, unknown, and removed keys to explicit defaults
or typed failures at the boundary.

## Typed DataStore

Use when the persisted value has a stable shape.

```kotlin
@Serializable
data class UserSettingsSnapshot(
    val showCompleted: Boolean = false,
    val sortOrder: String = "priority",
)

object UserSettingsSerializer : Serializer<UserSettingsSnapshot> {
    override val defaultValue = UserSettingsSnapshot()

    override suspend fun readFrom(input: InputStream): UserSettingsSnapshot =
        try {
            Json.decodeFromString(input.readBytes().decodeToString())
        } catch (error: SerializationException) {
            throw CorruptionException("Cannot read user settings", error)
        }

    override suspend fun writeTo(
        t: UserSettingsSnapshot,
        output: OutputStream,
    ) {
        output.write(Json.encodeToString(t).encodeToByteArray())
    }
}
```

Proto DataStore is preferred when the repo already uses protobuf or needs a
clear binary schema. JSON DataStore is acceptable when the repo already uses
kotlinx serialization and the object is small. Either way, keep the stored type
immutable and map it to repository/domain entities before crossing module
boundaries.

## Creation And DI

Create exactly one DataStore instance for a given file per process. Centralize
creation in DI or an app/data module:

```kotlin
@Provides
@Singleton
fun provideUserSettingsDataStore(
    @ApplicationContext context: Context,
): DataStore<UserSettingsSnapshot> =
    DataStoreFactory.create(
        serializer = UserSettingsSerializer,
        corruptionHandler = ReplaceFileCorruptionHandler {
            UserSettingsSnapshot()
        },
        produceFile = {
            context.dataStoreFile("user_settings.json")
        },
    )
```

Use `MultiProcessDataStoreFactory` only when separate Android processes must
read or write the same file. Do not mix single-process and multi-process
DataStore factories for the same file.

## Migration And Corruption

Before changing persisted data, document:

- old storage: SharedPreferences, previous JSON/proto schema, or app version
- new storage name and file
- default value for missing data
- migration order
- rollback or recovery behavior
- corruption handler behavior
- tests for missing, old, malformed, and current data

DataStore can migrate SharedPreferences, but migration is still a product data
change. Never silently drop user-visible preferences unless the product
explicitly accepts that behavior.

Use a corruption handler when unreadable data should recover to a default value.
If corruption means the account/session is unsafe, prefer a typed failure that
forces logout, reset, or re-authentication instead of pretending the default is
valid.

## Testing

Test these boundaries:

- defaults when the file does not exist
- read flow emits mapped repository/domain model
- write uses `updateData`/`edit` transactionally
- malformed data triggers corruption behavior or typed failure
- migration from SharedPreferences or previous schema
- two sequential writes produce the expected final value
- logout/account switch clears or switches the correct store
- UI observes ViewModel state instead of raw DataStore

Use temporary files or a fake repository/data source. Avoid tests that share the
real app DataStore file across cases.

## Do Not

- Do not create a DataStore instance inside a Composable.
- Do not expose `DataStore`, `Preferences`, generated proto classes, or
  serializer classes from repository APIs.
- Do not store large lists, relational records, messages, feeds, search indexes,
  or cache tables in DataStore.
- Do not use DataStore for partial updates or referential integrity.
- Do not mutate the stored type after reading it.
- Do not create multiple DataStore instances for the same file in one process.
- Do not mix single-process and multi-process factories for the same file.
- Do not add protobuf, kotlinx serialization, or DataStore dependencies to every
  module through broad build logic before at least two modules need them.
